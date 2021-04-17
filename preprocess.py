"""
Preprocess Script Created By Gabriel Orlanski.

Attempt to fix asdl errors

Arguments code is from: https://github.com/neulab/external-knowledge-codegen/blob/master/datasets
/conala/dataset.py
"""
import os
import argparse
from datasets.conala.dataset import preprocess_conala_dataset

if __name__ == '__main__':
    # Originally from dataset/conala/dataset.py, but when attempting to run it there,
    # I was getting import errors.
    arg_parser = argparse.ArgumentParser()
    #### General configuration ####
    arg_parser.add_argument('--pretrain', type=str, help='Path to pretrain file')
    arg_parser.add_argument('--out_dir', type=str, default='data/conala',
                            help='Path to output file')
    arg_parser.add_argument('--topk', type=int, default=0, help='First k number from mined file')
    arg_parser.add_argument('--freq', type=int, default=3, help='minimum frequency of tokens')
    arg_parser.add_argument('--vocabsize', type=int, default=20000,
                            help='First k number from pretrain file')
    arg_parser.add_argument('--include_api', type=str, help='Path to apidocs file')
    arg_parser.add_argument('--seed', type=int, help='Seed to use', default=1234)
    args = arg_parser.parse_args()

    args.out_dir = os.path.join(os.getcwd(), *args.out_dir.split(
        '/' if '/' in args.out_dir else "\\"))
    # the json files can be downloaded from http://conala-corpus.github.io
    preprocess_conala_dataset(train_file='data/conala/conala-train.json',
                              test_file='data/conala/conala-test.json',
                              mined_data_file=args.pretrain,
                              api_data_file=args.include_api,
                              grammar_file='asdl/lang/py3/py3_asdl.simplified.txt',
                              src_freq=args.freq, code_freq=args.freq,
                              vocab_size=args.vocabsize,
                              num_mined=args.topk,
                              out_dir=args.out_dir,
                              seed=args.seed)
