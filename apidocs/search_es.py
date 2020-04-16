import json
import pprint
import sys

from elasticsearch import Elasticsearch

def get_top_k(query, k=5):
    results = es.search(index='python-code', params={"q": query})['hits']['hits'][:k]
    for doc in results:
        print("Score: ", doc['_score'])
        print("Docstring: ", doc['_source']['doc']['docstring'])
        print("Code: ", doc['_source']['doc']['code'])
        print("URL: ", doc['_source']['doc']['url'])
        print("\n\n")

if __name__ == '__main__':
    es = Elasticsearch()
    query = sys.argv[1]
    get_top_k(query)