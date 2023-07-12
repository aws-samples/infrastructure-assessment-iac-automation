import aws_cdk as cdk
from aws_cdk import aws_cloudtrail as ct
from aws_cdk import aws_kms as kms
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_logs as logs

from constructs import Construct as construct

class Cloud_trail(construct):
    def __init__(self, scope: construct, id: str, identifier: str, bucket_name: s3.Bucket, kms_key: kms.Key, **kwargs):
        super().__init__(scope, id, **kwargs)
        ct_context = dict(self.node.try_get_context("ct_context"))
        ct_details = ct_context[identifier]
        trail_name=identifier+'-'+ct_details['name']

        self.cloud_trail= ct.Trail(self, trail_name,
            send_to_cloud_watch_logs=False,
            bucket=bucket_name,
            trail_name=ct_details['name'],
            is_multi_region_trail=True,
            enable_file_validation=True,
            encryption_key=kms_key,
            management_events=ct.ReadWriteType.ALL,
            )


        