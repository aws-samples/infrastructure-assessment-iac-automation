from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_cloudtrail as ct,
    aws_lambda_event_sources as lm_event_source,
    aws_s3 as s3
    # aws_sqs as sqs,
)
import aws_cdk as cdk

from constructs import Construct as construct

from . import s3constructs
from . import CloudtrailConstructs
from .import kmskey
from .import lambdaConstructs
from .import glueConstructs
from .import quickSightConstruct

class ResourceIaCStack(Stack):

    def __init__(self, scope: construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ### Creating S3 Buckets ##

        trail_s3_bucket = s3constructs.S3Buckets(self, 'cloudtrail-s3-bucket', identifier='ct')
        output_s3_bucket = s3constructs.S3Buckets(self, 'output-s3-bucket', identifier='output')
        output_s3_bucket.s3_bucket.add_lifecycle_rule(transitions=[s3.Transition(storage_class=s3.StorageClass.GLACIER,transition_after=Duration.days(30))])

        ### Creating KMS key for Cloud Trail ##
        kms_key = kmskey.Kms_Key(self, 'ct-kms_key', identifier='ct')


        ### Creating Lambda Function ##
        lambda_function = lambdaConstructs.lm_func(self, 'lambda-to-process-ct-logs', identifier='ct')

        ### Adding S3 event Trigger to Lambda Function ##
        lambda_function.lam_func.add_event_source(lm_event_source.S3EventSource(bucket=trail_s3_bucket.s3_bucket, events=[s3.EventType.OBJECT_CREATED],filters=[s3.NotificationKeyFilter(prefix=f"AWSLogs/{cdk.Aws.ACCOUNT_ID}/CloudTrail/")]))

        ## Add read policy for ct event bucket to lambda ##
        trail_bucket_arn=trail_s3_bucket.s3_bucket.bucket_arn
        trail_bucket_arn_path=trail_bucket_arn+'/*'
        lambda_function.lam_func.add_to_role_policy(iam.PolicyStatement(
            actions=['s3:Get*'],
            effect=iam.Effect.ALLOW,
            resources=[trail_bucket_arn_path]
        )
        )

        self.lambda_role_arn = lambda_function.lambda_role.role_arn
        kms_key.kms_key.add_to_resource_policy(iam.PolicyStatement(actions=["kms:Decrypt"],principals=[iam.ArnPrincipal(self.lambda_role_arn)],resources=["*"],effect=iam.Effect.ALLOW))

        ## Add write policy for output filtered event bucket to lambda ##
        output_s3_bucket_arn=output_s3_bucket.s3_bucket.bucket_arn
        output_s3_bucket_arn_path=output_s3_bucket_arn+'/*'
        lambda_function.lam_func.add_to_role_policy(iam.PolicyStatement(
            actions=['s3:ListMultipartUploadParts', 's3:PutObject', 's3:GetObject', 's3:AbortMultipartUpload', 'kms:Decrypt'],
            effect=iam.Effect.ALLOW,
            resources=[output_s3_bucket_arn_path,kms_key.kms_key.key_arn]
        ))

        ### Creating Cloud Trail #
        trail = CloudtrailConstructs.Cloud_trail(self, 'cloud_trail', bucket_name=trail_s3_bucket.s3_bucket, kms_key=kms_key.kms_key, identifier='ct')

        ### Create Glue Database ##
        output_s3_bucket_folder_arn=output_s3_bucket_arn+'/AWSLogs/'+cdk.Aws.ACCOUNT_ID+'/CloudTrail/*'
        output_s3_bucket_path=output_s3_bucket.s3_bucket.bucket_name+'/AWSLogs/'+cdk.Aws.ACCOUNT_ID+'/CloudTrail'

        glue_db = glueConstructs.Glue_DB(self, 'Resource-iac-glue-db', identifier='ct', output_s3_bucket_folder_arn=output_s3_bucket_folder_arn, output_s3_bucket_path=output_s3_bucket_path)

        #QuickSight setup - start
        #quicksight_athena = quickSightConstruct.QuickSight(self, 'operations-iac-qs-athena', identifier='ct')
        #quicksight_athena.node.add_dependency(glue_db)
        #QuickSight setup - ends
