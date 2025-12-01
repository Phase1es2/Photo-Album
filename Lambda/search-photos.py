import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

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


s3_client = boto3.client('s3') 


def query_opensearch(query):

    print("Executing OpenSearch Query:", json.dumps(query)) 
    
    try:
        response = opensearch_client.search(index='photos', body=query)
        

        print("OpenSearch Response (Success):", json.dumps(response)) 
        

        total_hits = response.get('hits', {}).get('total', {}).get('value', 0)
        print(f"Total photos found in OpenSearch: {total_hits}")

        return response['hits']['hits']
    except Exception as e:
        print(f"FATAL OpenSearch Connection/Search Error: {e}")
        return []


def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    try:
        query_params = event.get('queryStringParameters', {})
        keywords_str = query_params.get('q')
    except Exception:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing query parameter "q".'})
        }


    if not keywords_str:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'results': [], 'count': 0})
        }
    

    keywords = [keywords_str.lower()]
    print("Extracted Keywords:", keywords) 
    

    must_clauses = [{"match": {"labels": kw}} for kw in keywords]

    query = {
        "size": 20,
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }

    results = query_opensearch(query)
    
    photo_urls = []
    for hit in results:
        source = hit.get('_source', {})
        bucket_name = source.get('bucket')
        
        object_key = source.get('objectKey') 

        if bucket_name and object_key:
            try:
                presigned_url = s3_client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={
                        'Bucket': bucket_name,
                        'Key': object_key
                    },
                    ExpiresIn=3600
                )
                
                photo_urls.append({
                    'url': presigned_url,
                    'key': object_key 
                })
            except Exception as e:
                print(f"Error generating presigned URL for {object_key} in {bucket_name}: {e}")

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*'  
        },
        'body': json.dumps({
            'results': photo_urls,
            'count': len(photo_urls)
        })
    }