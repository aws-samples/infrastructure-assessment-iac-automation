from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_cloudtrail as ct,
    aws_lambda as lm
)
import aws_cdk as cdk
import os
from constructs import Construct as construct

class lm_func(construct):
    def __init__(self, scope: construct, id: str, identifier: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        lm_context = dict(self.node.try_get_context("lambda_context"))
        lm_details = lm_context[identifier]

        s3_context = dict(self.node.try_get_context("s3_context"))
        s3_details = s3_context['output']

        lm_name = identifier+'-'+lm_details['name']
        timeout = lm_details['timeout']
        memory_size = lm_details['memory_size']
        ephemeral_storage_size = lm_details['ephemeral_storage_size']
        relative_code_path=lm_details['relative_code_path']
        handler=lm_details['handler']
        fun_name=lm_details['name']
        env_variables = ({"OUTPUT_S3_BUCKET": s3_details['name']})

        self.lambda_role = iam.Role(self, id=fun_name+'-role',
                                assumed_by =iam.ServicePrincipal('lambda.amazonaws.com'),
                                managed_policies=[
                                iam.ManagedPolicy.from_aws_managed_policy_name(
                                    'service-role/AWSLambdaBasicExecutionRole')
                                ]
                                )

        self.lam_func = lm.Function(self, lm_name,
                              runtime=lm.Runtime.PYTHON_3_9,
                              handler=handler,
                              code=lm.Code.from_asset(os.path.join(os.path.dirname(__file__), relative_code_path)),
                              timeout=cdk.Duration.seconds(timeout),
                              memory_size=memory_size,
                              ephemeral_storage_size=cdk.Size.mebibytes(ephemeral_storage_size),
                              function_name=fun_name,
                              role=self.lambda_role,
                              environment=env_variables,
                              reserved_concurrent_executions=20
                              )
