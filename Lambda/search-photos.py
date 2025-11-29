import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth


# Lex-Bot
lex_bot = boto3.client('lexv2-runtime')
BOT_ID = 'HQYG2VEI9R'
BOT_ALIAS_ID = 'TSTALIASID'
LOCALE_ID = 'en_US'


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
    try:
        response = opensearch_client.search(index='photos', body=query)
        return response['hits']['hits']
    except Exception as e:
        print(f"OpenSearch Error: {e}")
        return []


def get_slots(intent_request):
    return intent_request['sessionState']['intent']['slots']

def get_keyword():
    q_slot = slots.get('q')
    keywords = []
    if q_slot:
        if 'values' in q_slot:
            for item in q_slot['values']:
                val = item['value'].get('interpretedValue') or item['value'].get('originalValue')
                keywords.append(val)
        elif 'value' in q_slot:
            val = q_slot['value'].get('interpretedValue') or q_slot['value'].get('originalValue')
            keywords.append(val)
    return keywords

def lambda_handler(event, context):
    print("Event:", json.dumps(event))

    slots = get_slots(event)
    q_slot = slots.get('q')
    
    keywords = get_keyword(slots)

    print("Extracted Keywords:", keywords) 

    if not keywords:
        return close(event, "Fulfilled", "I didn't understand what you want to search.")

    must_clauses = []
    for kw in keywords:
        must_clauses.append({
            "match": {
                "labels": kw
            }
        })

    query = {
        "size": 20,
        "query": {
            "bool": {
                "must": must_clauses
            }
        }
    }


    results = query_opensearch(query)
    count = len(results)


    return close(event, "Fulfilled", f"I found {count} photos that match all your keywords: {', '.join(keywords)}.")


def close(event, fulfillment_state, message_content):
    return {
        "sessionState": {
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": event['sessionState']['intent']['name'],
                "state": fulfillment_state
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message_content
            }
        ]
    }