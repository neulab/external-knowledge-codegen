#!/bin/bash

# test_file="data/conala/test.var_str_sep.bin"
test_file="data/conala/test.bin"
reranker_file="best_pretrained_models/reranker.conala.vocab.src_freq3.code_freq3.mined_100000.intent_count100k_topk1_temp5.bin"
python exp.py \
    --cuda \
    --mode test \
    --load_model $1 \
    --load_reranker $reranker_file \
    --beam_size 15 \
    --test_file ${test_file} \
    --evaluator conala_evaluator \
    --save_decode_to decodes/conala/$(basename $1).test.decode \
    --decode_max_time_step 100

