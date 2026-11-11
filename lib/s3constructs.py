import aws_cdk as cdk
from aws_cdk import aws_s3 as s3

from constructs import Construct as construct

class S3Buckets(construct):
    def __init__(self, scope: construct, id: str, identifier: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        s3_context = dict(self.node.try_get_context("s3_context"))
        s3_details = s3_context[identifier]

        # The bucket name is not set, so AWS CDK generates a unique name. This
        # avoids collisions with (and squatting of) predictable bucket names.
        self.s3_bucket = s3.Bucket(self, identifier+'-'+s3_details['name'],
                              encryption=s3.BucketEncryption.S3_MANAGED,
                              server_access_logs_prefix="bucket-access-logs",
                              enforce_ssl=True,
                              block_public_access=s3.BlockPublicAccess.BLOCK_ALL
                              )
