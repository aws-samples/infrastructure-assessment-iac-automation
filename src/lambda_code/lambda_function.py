import json
import urllib.parse
import boto3
import os
import gzip
import json
import io
from botocore.exceptions import ClientError

region =  os.getenv('AWS_REGION','us-west-2')
output_bucket  = os.getenv('OUTPUT_S3_BUCKET','resource-output-bucket')
s3_client = boto3.client('s3', region_name = region)

DATA_DICT = {  'AWS-CDK': ['cdk'],
        'Terraform': ['Terraform'],
        'AWS-CLI': ['aws-cli'],
        'AWS-Console': ['Console'],
        'AWS SSM Agent': ['amazon-ssm-agent'],
        'BOTO3 SDK': ['boto3'],
        'Browser': ['Mozilla','Safari','Chrome']
        }

def get_trail_data(bucket,key):
    try:
            response = s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read()
            with gzip.GzipFile(fileobj=io.BytesIO(content), mode='rb') as fh:
                return (json.load(fh))
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e

def extract_data(record):
     output = {}
     user_identity_record = record.get('userIdentity',{})
     if user_identity_record:
        output['principal_id'] = user_identity_record.get('principalId','')
        output['account_id'] = user_identity_record.get('accountId','')
        output['invoked_by'] = user_identity_record.get('invokedBy','')
        session_context = user_identity_record.get('sessionContext',{})
        if session_context:
            sessionIssuer = session_context.get('sessionIssuer',{})
            if sessionIssuer:
                output['session_user'] = sessionIssuer.get('userName','')
        else:
            output['session_user'] = ''
     output['event_time'] = record.get('eventTime','')
     output['event_source'] = record.get('eventSource','')
     output['event_name'] =  record.get('eventName','')
     output['user_agent'] = record.get('userAgent','')
     output['tool'] = get_iac_tool(output['invoked_by'],output['session_user'],output['user_agent'])
     if output['tool'] == output['user_agent']:
        print(f'Could not find for request where request:{record}')
     output['resource'] = json.dumps(record.get('requestParameters',{}))

     return output




def get_iac_tool(invoked_by,session_user,user_agent):

    for k in DATA_DICT:
        for v in DATA_DICT[k]:
            if v.lower() in user_agent.lower():
                return k

    if invoked_by == 'cloudformation.amazonaws.com':
        if 'cdk' in session_user:
            return 'AWS-CDK'
        return 'CloudFormation'
    elif 'aws-sdk-' in user_agent:
        return user_agent.split('/')[0]
    elif 'aws-sdk-' in user_agent and 'amazon-ssm-agent' in user_agent:
        return user_agent.split('/')[0]
    elif 'amazonaws.com' in user_agent:
        return f'AWS {user_agent.split(".")[0]}'
    else:
        return user_agent


def lambda_handler(event, context):
    source_bucket = event['Records'][0]['s3']['bucket']['name']
    source_key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    output_key=source_key.replace('json.gz','json')
    trail_data = get_trail_data(source_bucket,source_key)
    output_temp_file = f'/tmp/{output_key.split("/")[-1]}'

    with open(output_temp_file, 'w') as f:
        for record in trail_data['Records']:
            if not record['readOnly']:
                if record['eventName'] != 'CreateLogStream':
                    json.dump(extract_data(record), f)

    try:
        response = s3_client.upload_file(output_temp_file, output_bucket, output_key)
    except ClientError as e:
        print(e)
        raise e from ClientError