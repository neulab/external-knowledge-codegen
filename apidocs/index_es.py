import json

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys

es = Elasticsearch()

print(es.indices.create(index='python-code', ignore=400))

jsonl_file = "python_docs.jsonl"

def gendata(filename):
    with open(filename, encoding='utf-8') as jsonl:
        for line in jsonl:
            doc = json.loads(line)
            result = {
                "_index": "python-code",
                "_type": "document"
            }
            for k, v in doc.items():
                result[k] = v
            return result

print(bulk(es, gendata(jsonl_file)))


if __name__ == '__main__':
    index_name, json_file = sys.argv[1:]
    print('create index')
    print(es.indices.create(index=index_name, ignore=400))

    print('index docs')
    print(bulk(es, gendata(json_file)))
