import aws_cdk as cdk
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam

from constructs import Construct as construct

class Glue_DB(construct):
    def __init__(self, scope: construct, id: str, identifier: str, output_s3_bucket_folder_arn: str, output_s3_bucket_path: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        glue_context = dict(self.node.try_get_context("glue_context"))
        glue_details = glue_context[identifier]
        glue_name = identifier+'-'+glue_details['name']
        db_name = glue_details['name']
        crawler_name = glue_details['crawler_name']
        cr_logical_name = identifier+'-'+glue_details['crawler_name']

        self.glue_role = iam.Role(self, identifier+'glue_role',
                      description='Role for Glue services to access S3',
                      assumed_by=iam.ServicePrincipal('glue.amazonaws.com'),
                      inline_policies={'resource_iac_glue_policy': iam.PolicyDocument(
                          statements=[iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=['s3:GetObject', 's3:PutObject'],
                            resources=[output_s3_bucket_folder_arn])])},
                      managed_policies=[
                                iam.ManagedPolicy.from_aws_managed_policy_name(
                                    'service-role/AWSGlueServiceRole')
                                ]
                            )

        self.glue_db = glue.CfnDatabase(self, glue_name,
                                        catalog_id=cdk.Aws.ACCOUNT_ID,
                                        database_input=glue.CfnDatabase.DatabaseInputProperty(
                                            name=db_name,
                                            description='Database to store resource event details.'
                                        )
                                        )
        glue_crawler=glue.CfnCrawler(self, cr_logical_name,
                                     name=crawler_name,
                                     database_name=db_name,
                                     table_prefix='resource_iac_data_',
                                     role=self.glue_role.role_arn,
                                     schedule=glue.CfnCrawler.ScheduleProperty(
                                     schedule_expression="cron(10 5 * * ? *)"
                                     ),
                                     targets=glue.CfnCrawler.TargetsProperty(
                                        s3_targets=[glue.CfnCrawler.S3TargetProperty(
                                        path=f's3://{output_s3_bucket_path}/'
                                     )]))
