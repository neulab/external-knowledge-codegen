from typing import List
import json
import pprint
import sys
import argparse
import re
from tqdm import tqdm
import string
from collections import defaultdict
from elasticsearch import Elasticsearch
import operator
import numpy as np
import pickle

#PUNCT_TO_SPACE = dict(zip(list(string.punctuation), list(' ' * len(string.punctuation))))
PUNCT_TO_SPACE = str.maketrans(string.punctuation, ' ' * len(string.punctuation))

def softmax(x):
    e_x = np.exp(x - np.max(x))
    return e_x / e_x.sum()

def log_softmax(x):
    return np.log(softmax(x))

class ESSearcher():
    def __init__(self, index_name: str):
        self.es = Elasticsearch()
        self.index_name = index_name

    def query_format(self, query_str: str, field: str):
        new_query_str = query_str.translate(PUNCT_TO_SPACE)
        new_query_str = ' '.join([w for w in new_query_str.split() if re.match('^[0-9A-Za-z]+$', w)])
        new_query_str = new_query_str.replace(' AND ', ' ').replace(' and ', ' ')
        '''
        if len(query_str) - len(new_query_str) > 10:
            print(query_str)
            print(new_query_str)
            input()
        '''
        return '{}:({})'.format(field, new_query_str)

    def get_topk(self, query_str: str, field: str, topk: int=5):
        results = self.es.search(
            index=self.index_name, 
            q=self.query_format(query_str, field))['hits']['hits'][:topk]
        return [(doc['_source'], doc['_score']) for doc in results]

def load_multi_files(files: List[str], max_counts: List[int]=None):
    if type(files) is not list:
        files = [files]
    dataset = []
    max_counts = max_counts or [None] * len(files)
    for file, max_count in zip(files, max_counts):
        try:
            td = json.load(open(file, 'r'))
        except:
            td = [json.loads(l) for l in open(file, 'r')]
        if max_count:
            td = td[:max_count]
        print('load {} from {}'.format(len(td), file))
        dataset.extend(td)
    return dataset

def aug_iter(ess, dataset, field, topk):
    '''
    iterate over dataset and do retrieval
    '''
    for i, code in enumerate(tqdm(dataset)):
        if field == 'intent':
            query = (code['rewritten_intent'] if 'rewritten_intent' in code else None) or code['intent']
        elif field == 'snippet':
            query = code['snippet']
        try:
            hits = ess.get_topk(query, field, topk=topk)
            yield code, hits
        except KeyboardInterrupt:
            raise
        except Exception as e:
            pass  # sometimes the query is empty

def topk_aug(args):
    dataset = load_multi_files(args.inp.split(':'))
    ess = ESSearcher(index_name='python-docs')

    aug_dataset = []
    id2count = defaultdict(lambda: 0)
    for code, hits in aug_iter(ess, dataset, args.field, args.topk):
        '''
        if len(hits) != args.topk:
            print('not enough for "{}"'.format(query))
            print(ess.query_format(query, args.field))
        '''
        for (rcode, score) in hits:
            rcode['for'] = code['question_id']
            rcode['retrieval_score'] = score
            aug_dataset.append(rcode)
            id2count[rcode['question_id']] += 1
    
    with open(args.out, 'w') as fout:
        for code in aug_dataset:
            fout.write(json.dumps(code) + '\n')

    print('most commonly retrieved ids {}'.format(sorted(id2count.items(), key=lambda x: -x[1])[:5]))

def anneal(probs: np.ndarray, temperature=1):
    lp = np.log(probs)
    alp = temperature * lp
    anneal_probs = softmax(alp)
    return anneal_probs

def get_distribution(args):
    files = args.inp.split(':')
    dataset = load_multi_files(files, max_counts=[args.max_count] * len(files))
    ess = ESSearcher(index_name='python-docs')

    aug_dataset = []
    id2count = defaultdict(lambda: 0)
    for code, hits in aug_iter(ess, dataset, args.field, args.topk):
        for (rcode, score) in hits:
            rcode['for'] = code['question_id']
            rcode['retrieval_score'] = score
            aug_dataset.append(rcode)
            id2count[rcode['question_id']] += 1

    # compute distribution
    dist = sorted(id2count.items(), key=lambda x: -x[1])
    qids = np.array(list(map(operator.itemgetter(0), dist)))
    probs = np.array(list(map(operator.itemgetter(1), dist)))
    probs = probs / np.sum(probs)

    if args.temp:  # anneal
        probs = anneal(probs, args.temp)

    print('#retrieved code {}'.format(len(probs)))
    print('most commonly retrieved ids {}'.format(list(zip(qids, probs))[:5]))

    if args.out:
        with open(args.out, 'w') as fout:
            for qid, ap in zip(qids, probs):
                fout.write('{}\t{}\n'.format(qid, ap))

def sample_aug(args):
    dist_file, data_file = args.inp.split(':')
    qids = []
    probs = []
    with open(dist_file, 'r') as fin:
        for l in fin:
            qid, prob = l.strip().split('\t')
            qids.append(qid)
            probs.append(float(prob))
    qids = np.array(qids)
    probs = np.array(probs)

    if args.temp:  # anneal
        print('annel to {}'.format(args.temp))
        print(probs[:5])
        probs = anneal(probs, args.temp)
        print(probs[:5])

    dataset = load_multi_files(data_file)
    qid2code = dict((str(code['question_id']), code) for code in dataset)
    qid2count = defaultdict(lambda: 0)
    with open(args.out, 'w') as fout:
        for sam in np.random.choice(len(probs), args.max_count, p=probs):
            fout.write(json.dumps(qid2code[qids[sam]]) + '\n')
            qid2count[qids[sam]] += 1

    print('mostly sampled qids {}'.format(sorted(qid2count.items(), key=lambda x: -x[1])[:5]))


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--method', type=str, help='method of augmentation', 
        choices=['topk', 'dist', 'sample'])
    arg_parser.add_argument('--inp', type=str, help='input json file')
    arg_parser.add_argument('--out', type=str, help='output file')
    arg_parser.add_argument('--topk', type=int, help='top k for retrieval', default=5)
    arg_parser.add_argument('--max_count', type=int, 
        help='max number of codes from each file', default=None)
    arg_parser.add_argument('--field', type=str, help='field for retrieval', 
        choices=['snippet', 'intent'], default='snippet')
    arg_parser.add_argument('--temp', type=float, help='temperature of sampling', default=None)
    args = arg_parser.parse_args()

    if args.method == 'topk':
        topk_aug(args)
    elif args.method == 'dist':
        get_distribution(args)    
    elif args.method == 'sample':
        sample_aug(args)
