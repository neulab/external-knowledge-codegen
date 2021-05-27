import json

import argparse
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
import sys

es = Elasticsearch()


def gendata(filename, index_name):
    with open(filename, encoding='utf-8') as jsonl:
        for line in jsonl:
            doc = json.loads(line)
            result = {
                "_index": index_name,
                "_type": "document"
            }
            for k, v in doc.items():
                result[k] = v
            yield result

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument('index_name',
                            default='python-code',
                            nargs='?',
                            type=str,
                            help='Set the name of the ElasticSearch index.')
    arg_parser.add_argument('json_file',
                            default='python-docs.jsonl',
                            nargs='?',
                            type=str,
                            help='Set the file to index.')
    args = arg_parser.parse_args()

    print('create index')
    print(es.indices.create(index=args.index_name, ignore=400))

    print('index docs')
    data = gendata(args.json_file, args.index_name)
    res = bulk(es, data)
    print(res)
