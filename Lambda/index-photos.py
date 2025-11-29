import json
import boto3
import urllib.parse
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

# Elastic Search
region = 'us-east-1'
host = 'search-photos-tdaddyd45xyfcfqmv4lm24uc3u.aos.us-east-1.on.aws' 
session = boto3.Session()
credentials = session.get_credentials()

auth = AWSV4SignerAuth(credentials, region)

opensearch_client = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection,
)

def get_labels(bucket, key):
    """Return ONLY the label names from Rekognition."""
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=15,
        MinConfidence=70
    )

    labels = [label['Name'].lower() for label in response['Labels']]

    print("Detected labels:")
    for l in labels:
        print(f"- {l}")

    return labels


def get_s3_metadata_labels(bucket, key):
    """Retrieve customLabels from S3 metadata and return A1 as a list."""
    response = s3.head_object(Bucket=bucket, Key=key)
    metadata = response.get("Metadata", {})

    print("HEAD METADATA:", metadata)

    custom = metadata.get("customlabels")  # lowercase

    if custom:
        A1 = [x.strip() for x in custom.split(",") if x.strip()]
    else:
        A1 = []

    print("Custom Labels A1:", A1)
    return A1
    

def save_to_opensearch(document):
    try:
        response = opensearch_client.index(
            index='photos',
            body=document,
            id=document['objectKey']
        )
        print("Data indexed successfully:", response)
        return True
    except Exception as e:
        print(f"Error indexing data: {e}")
        return False


def process_image(bucket, key):
    meta_labels = get_s3_metadata_labels(bucket, key)

    rek_labels = get_labels(bucket, key)

    # Combine both → remove duplicates
    labels = list(set(meta_labels + rek_labels))

    print("Final Labels:", labels)

    doc = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.utcnow().isoformat(),
        "labels": labels
    }
    # Save to OpenSearch
    save_to_opensearch(doc)
    return doc


def lambda_handler(event, context):

    print("Event", json.dumps(event, indent=2))

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8'
    )

    print(f"Processing image: s3://{bucket}/{key}")

    doc = process_image(bucket, key)

    print("Document to store:", json.dumps(doc, indent=2))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Image processed!',
            'document': doc,
        })
    }