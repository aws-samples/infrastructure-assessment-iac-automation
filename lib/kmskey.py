import aws_cdk as cdk
from aws_cdk import aws_kms as kms
from aws_cdk import aws_iam as iam

from constructs import Construct as construct

class Kms_Key(construct):
    def __init__(self, scope: construct, id: str, identifier: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        kms_context = dict(self.node.try_get_context("kms_context"))
        kms_details = kms_context[identifier]
        kms_name = identifier+'-'+kms_details['name']

        ct_context = dict(self.node.try_get_context("ct_context"))
        trail_name = ct_context[identifier]['name']

        stack = cdk.Stack.of(self)
        # ARN of the trail created by this stack. Used to scope the key policy so
        # that only this account's trail can use the key (confused deputy protection).
        trail_arn = stack.format_arn(service='cloudtrail', resource='trail', resource_name=trail_name)
        account_trails_arn = 'arn:{}:cloudtrail:*:{}:trail/*'.format(stack.partition, stack.account)

        self.kms_key = kms.Key(self, kms_name,
                          description = "{}-key-ct".format(kms_name),
                          enable_key_rotation=True,
                          )
        self.kms_key.add_alias(
            alias_name = 'alias/{}-key-ct'.format(kms_name)
        )

        cloudtrail_principal = iam.ServicePrincipal('cloudtrail.amazonaws.com')

        self.kms_key.add_to_resource_policy(iam.PolicyStatement(
            sid='AllowCloudTrailToEncryptLogs',
            effect=iam.Effect.ALLOW,
            principals=[cloudtrail_principal],
            actions=['kms:GenerateDataKey*'],
            resources=['*'],
            conditions={
                'StringEquals': {'aws:SourceArn': trail_arn},
                'StringLike': {'kms:EncryptionContext:aws:cloudtrail:arn': account_trails_arn},
            },
        ))

        self.kms_key.add_to_resource_policy(iam.PolicyStatement(
            sid='AllowCloudTrailToDescribeKey',
            effect=iam.Effect.ALLOW,
            principals=[cloudtrail_principal],
            actions=['kms:DescribeKey'],
            resources=['*'],
            conditions={
                'StringEquals': {'aws:SourceArn': trail_arn},
            },
        ))
