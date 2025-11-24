import json
import boto3
import urllib.parse
from datetime import datetime

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')

def get_labels(bucket, key):
    """Return ONLY the label names from Rekognition."""
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=10,
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


def elastic_search_json(bucket, key):
    # A1 = metadata labels
    A1 = get_s3_metadata_labels(bucket, key)

    # A2 = rekognition labels (list)
    A2 = get_labels(bucket, key)

    # Combine both → remove duplicates
    final_labels = list(set(A1 + A2))

    print("Final Labels:", final_labels)

    document = {
        "objectKey": key,
        "bucket": bucket,
        "createdTimestamp": datetime.utcnow().isoformat(),
        "labels": final_labels
    }

    return document


def lambda_handler(event, context):

    print("Event", json.dumps(event, indent=2))

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(
        event['Records'][0]['s3']['object']['key'], encoding='utf-8'
    )

    print(f"Processing image: s3://{bucket}/{key}")

    doc = elastic_search_json(bucket, key)

    print("Document to store:", json.dumps(doc, indent=2))

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Image processed!',
            'document': doc,
        })
    }