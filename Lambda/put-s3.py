import json
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    response_headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,x-amz-meta-customLabels',
        'Access-Control-Allow-Methods': 'OPTIONS,POST,PUT'
    }

    try:
        body = json.loads(event['body'])
        filename = body.get('filename')
        file_type = body.get('filetype')

        custom_labels = body.get('customLabels', '')


        s3_params = {
            'Bucket': 'majin-photo-storage',
            'Key': filename,
            'ContentType': file_type,
            'Metadata': {
                'customLabels': custom_labels 
            }
        }

        upload_url = s3_client.generate_presigned_url(
            'put_object',
            Params=s3_params,
            ExpiresIn=300
        )

        return {
            'statusCode': 200,
            'headers': response_headers,
            'body': json.dumps({'uploadURL': upload_url})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'headers': response_headers,
            'body': json.dumps({'error': str(e)})
        }