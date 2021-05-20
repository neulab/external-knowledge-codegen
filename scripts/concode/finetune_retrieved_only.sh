#!/bin/bash
set -e

seed=0
mined_num=50000
ret_method=$1
pretrained_model_name=$2
freq=3
vocab="data/concode/vocab.src_freq${freq}.code_freq${freq}.bin"
finetune_file="data/concode/train.all_0.bin"
dev_file="data/concode/dev.bin"
dropout=0.3
hidden_size=256
embed_size=128
action_embed_size=128
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=15
model_name=finetune.retapi_only.dr${dropout}.lr${lr}.lr_de${lr_decay}.lr_da${lr_decay_after_epoch}.beam${beam_size}.seed${seed}.${ret_method}5

echo "**** Writing results to logs/concode/${model_name}.log ****"
mkdir -p logs/concode
echo commit hash: "$(git rev-parse HEAD)" > logs/concode/"${model_name}".log

#     --cuda \
python -u exp.py \
    --seed ${seed} \
    --mode train \
    --batch_size 10 \
    --evaluator concode_evaluator \
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
    --patience 5 \
    --max_num_trial 5 \
    --glorot_init \
    --lr ${lr} \
    --lr_decay ${lr_decay} \
    --lr_decay_after_epoch ${lr_decay_after_epoch} \
    --max_epoch 80 \
    --beam_size ${beam_size} \
    --log_every 50 \
    --save_to saved_models/concode/${model_name} 2>&1 | tee logs/concode/${model_name}.log

. scripts/concode/test.sh saved_models/concode/${model_name}.bin 2>&1 | tee -a logs/concode/${model_name}.log
