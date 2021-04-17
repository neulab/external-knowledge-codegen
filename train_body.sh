#!/bin/bash
set -e

seed=0
freq=3
vocab=$3
#vocab="data/conala/vocab.src_freq3.code_freq3.mined_100000.goldmine_snippet_count100k_topk1_temp2.bin"
train_file=$1
dev_file="data/conala/dev.bin"
dropout=0.3
hidden_size=256
embed_size=512
action_embed_size=512
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
batch_size=32
max_epoch=$4
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=10
model_name=$2
valid_every_epoch=$5
echo "**** Writing results to logs/conala/${model_name}.log ****"
echo $valid_every_epoch
mkdir -p logs/conala
echo commit hash: `git rev-parse HEAD` > logs/conala/${model_name}.log

python -u exp.py \
    --cuda \
    --seed ${seed} \
    --mode train \
    --batch_size ${batch_size} \
    --evaluator conala_evaluator \
    --asdl_file asdl/lang/py3/py3_asdl.simplified.txt \
    --transition_system python3 \
    --train_file ${train_file} \
    --dev_file ${dev_file} \
    --vocab ${vocab} \
    --lstm ${lstm} \
    --valid_every_epoch valid_every_epoch \ 
    --no_parent_field_type_embed \
    --no_parent_production_embed \
    --hidden_size ${hidden_size} \
    --embed_size ${embed_size} \
    --action_embed_size ${action_embed_size} \
    --field_embed_size ${field_embed_size} \
    --type_embed_size ${type_embed_size} \
    --dropout ${dropout} \
    --patience 5 \
    --max_num_trial 5 \
    --glorot_init \
    --lr ${lr} \
    --lr_decay ${lr_decay} \
    --lr_decay_after_epoch ${lr_decay_after_epoch} \
    --max_epoch ${max_epoch} \
    --beam_size ${beam_size} \
    --log_every 50 \
    --save_to saved_models/conala/${model_name} 2>&1 | tee logs/conala/${model_name}.log
