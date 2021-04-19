#!/bin/bash
set -e

seed=$6
pretrained_model_name=$1
vocab=$2
finetune_file=$3
dev_file="data/conala/dev.bin"
dropout=0.3
hidden_size=256
embed_size=512
action_embed_size=512
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=15
model_name=$4

valid_every_epoch=$5
echo "**** Writing results to logs/conala/${model_name}.log ****"
mkdir -p logs/conala
echo commit hash: "$(git rev-parse HEAD)" > logs/conala/"${model_name}".log

python -u exp.py \
    --cuda \
    --seed ${seed} \
    --mode train \
    --batch_size 32 \
    --evaluator conala_evaluator \
    --asdl_file asdl/lang/py3/py3_asdl.simplified.txt \
    --transition_system python3 \
    --train_file ${finetune_file} \
    --dev_file ${dev_file} \
    --pretrain ${pretrained_model_name} \
    --vocab ${vocab} \
    --lstm ${lstm} \
    --no_parent_field_type_embed \
    --no_parent_production_embed \
    --hidden_size ${hidden_size} \
    --embed_size ${embed_size} \
    --action_embed_size ${action_embed_size} \
    --field_embed_size ${field_embed_size} \
    --type_embed_size ${type_embed_size} \
    --dropout ${dropout} \
    --valid_every_epoch ${valid_every_epoch} \
    --patience ${6:-3} \
    --max_num_trial 5 \
    --glorot_init \
    --lr ${lr} \
    --lr_decay ${lr_decay} \
    --lr_decay_after_epoch ${lr_decay_after_epoch} \
    --max_epoch 80 \
    --beam_size ${beam_size} \
    --log_every 50 \
    --save_to saved_models/conala/${model_name} 2>&1 | tee logs/conala/${model_name}.log
