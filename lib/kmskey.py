import aws_cdk as cdk
from aws_cdk import aws_cloudtrail as ct
from aws_cdk import aws_kms as kms
from aws_cdk import aws_ssm as ssm
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_iam as iam

from constructs import Construct as construct

class Kms_Key(construct):
    def __init__(self, scope: construct, id: str, identifier: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        kms_context = dict(self.node.try_get_context("kms_context"))
        kms_details = kms_context[identifier]
        kms_name = identifier+'-'+kms_details['name']

        self.kms_key = kms.Key(self, kms_name,
                          description = "{}-key-ct".format(kms_name),
                          enable_key_rotation=True,

                          )
        self.kms_key.add_alias(

            alias_name = 'alias/{}-key-ct'.format(kms_name)
        )

        self.kms_key.grant_encrypt_decrypt(iam.ServicePrincipal('cloudtrail.amazonaws.com'))
