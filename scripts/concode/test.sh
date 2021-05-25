#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

test_file="data/concode/test.bin"
# reranker_file="best_pretrained_models/reranker.concode.vocab.src_freq3.code_freq3.mined_100000.intent_count100k_topk1_temp5.bin"
#     --cuda \
#     --load_reranker $reranker_file \
python exp.py \
    --mode test \
    --load_model $1 \
    --beam_size 15 \
    --test_file ${test_file} \
    --evaluator concode_evaluator \
    --save_decode_to decodes/concode/$(basename $1).test.decode \
    --decode_max_time_step 100 \
    --root_production "typedeclaration,MethodDeclaration"

