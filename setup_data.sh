#!/bin/bash
set -e

SDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WDIR=`pwd`



# Extract data
cd $WDIR/data


# Get the data
wget http://www.phontron.com/download/conala-corpus-v1.1.zip
unzip conala-corpus-v1.1.zip

mv -f conala-corpus/* conala

# Delete files
rm conala-corpus-v1.1.zip
rm -rf conala-corpus

cd $SDIR

python preprocess.py --pretrain data/conala/conala-mined.jsonl --topk 100000 --include_api apidocs/processed/distsmpl/snippet_15k/goldmine_snippet_count100k_topk1_temp2.jsonl

echo "Done with Preprocessing" 
