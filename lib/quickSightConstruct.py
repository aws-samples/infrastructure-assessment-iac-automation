import aws_cdk as cdk
from aws_cdk import aws_quicksight as quicksight

from constructs import Construct as construct

class QuickSight(construct):
    def __init__(self, scope: construct, id: str, identifier: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        qs_context = dict(self.node.try_get_context("qs_context"))
        qs_details = qs_context[identifier]
        qs_principal_arn = "arn:aws:quicksight:"+qs_details['group_region']+":"+cdk.Aws.ACCOUNT_ID+":group/"+qs_details['qs_namespace']+"/"+qs_details['group_name']
        qs_data_source_permissions = [
            quicksight.CfnDataSource.ResourcePermissionProperty(
                principal=qs_principal_arn,
                actions=[
                    "quicksight:DescribeDataSource",
                    "quicksight:DescribeDataSourcePermissions",
                    "quicksight:PassDataSource",
                    "quicksight:UpdateDataSource",
                    "quicksight:DeleteDataSource",
                    "quicksight:UpdateDataSourcePermissions"
                ],
            ),
        ]

        qs_dataset_permissions = [
            quicksight.CfnDataSet.ResourcePermissionProperty(
                principal=qs_principal_arn,
                actions=[
                    "quicksight:DescribeDataSet",
                    "quicksight:DescribeDataSetPermissions",
                    "quicksight:PassDataSet",
                    "quicksight:DescribeIngestion",
                    "quicksight:ListIngestions",
                    "quicksight:UpdateDataSet",
                    "quicksight:DeleteDataSet",
                    "quicksight:CreateIngestion",
                    "quicksight:CancelIngestion",
                    "quicksight:UpdateDataSetPermissions"
                ],
            )
        ]

        resource_dasboard_source = quicksight.CfnDataSource(self, identifier+'-'+qs_details['name'],
                                                            aws_account_id=cdk.Aws.ACCOUNT_ID,
                                                            data_source_id=identifier+'-'+qs_details['name']+'-datasource',
                                                            type="ATHENA",
                                                            name=identifier+'-'+qs_details['name']+'-datasource',
                                                            permissions=qs_data_source_permissions
                                                            )

        qs_athena_dataset_resource_iac_physical_table = (
            quicksight.CfnDataSet.PhysicalTableProperty(
                relational_table=quicksight.CfnDataSet.RelationalTableProperty(
                    data_source_arn=resource_dasboard_source.attr_arn,
                    input_columns=[
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="principal_id", type="STRING"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="account_id", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="invoked_by", type="STRING"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="session_user", type="STRING"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="event_time", type="DECIMAL"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="event_source", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="event_name", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="user_agent", type="DECIMAL"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="tool", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="resource", type="STRING"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="partition_0", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="partition_1", type="DECIMAL"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="partition_2", type="INTEGER"
                        ),
                        quicksight.CfnDataSet.InputColumnProperty(
                            name="partition_3", type="INTEGER"
                        ),
                    ],
                    catalog="AWSDataCatalog",
                    schema=qs_details['db_name'],
                    name=qs_details['table_name'],
                )
            )
        )

        resource_dataset = quicksight.CfnDataSet(self, identifier+'-'+qs_details['ds_name'],
                                                 data_set_id=identifier+'-'+qs_details['ds_name'],
                                                 name = identifier+'-'+qs_details['ds_name'],
                                                 aws_account_id=cdk.Aws.ACCOUNT_ID,
                                                 import_mode="DIRECT_QUERY",
                                                 physical_table_map={
                                                     "resource-iac-table":  qs_athena_dataset_resource_iac_physical_table
                                                 },
                                                 permissions=qs_dataset_permissions
        )
