#!/bin/bash

decode_file=$1
model_file=$2
out_name=$3

python exp.py \
    --cuda \
    --mode test \
    --load_model "${model_file}" \
    --beam_size 15 \
    --test_file "${decode_file}" \
    --evaluator conala_evaluator \
    --save_decode_to "decodes/conala/${out_name}.$(basename ${decode_file}).decode" \
    --decode_max_time_step 100
