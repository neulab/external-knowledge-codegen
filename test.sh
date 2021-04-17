#!/bin/bash
WDIR=`pwd`

test_file=data/conala/test.bin
seed=0
beam_size=15
model_name=$1
decode_name=$2
echo $model_path
echo "**** Writing results to logs/conala/${model_name}.log ****"
mkdir -p logs/conala
#echo commit hash: `git rev-parse HEAD` > logs/conala/${model_name}.log

python -u exp.py \
    --cuda \
    --mode test \
    --load_model ${model_name}.bin 2>&1 \
    --beam_size 15 \
    --test_file ${test_file} \
    --evaluator conala_evaluator \
    --save_decode_to decodes/conala/${decode_name}.test.decode \
    --decode_max_time_step 100 | tee -a logs/conala/${model_name}.log
