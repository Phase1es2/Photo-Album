import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


# Elastic Search
region = 'us-east-1'
host = 'search-photos-tdaddyd45xyfcfqmv4lm24uc3u.aos.us-east-1.on.aws'

session = boto3.Session()
credentials = session.get_credentials()
auth = AWSV4SignerAuth(credentials, region)

opensearch_client = OpenSearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=auth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,
)


def query_opensearch(query):
    response = opensearch_client.search(index='photos', body=query)
    return response['hits']['hits']


def lambda_handler(event, context):
    key1 = 'people'
    key2 = 'portrait'
    print(f'Search for: {key1} {key2}')

    query = {
        "query": {
            "bool": {
                "must": [
                    {"match": {"labels": key1}},
                    {"match": {"labels": key2}}
                ]
            }
        }
    }

    results = query_opensearch(query)


    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }