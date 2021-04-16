#!/bin/bash
set -e

seed=0
mined_num=10000
freq=3
vocab="data/conala/vocab.src_freq${freq}.code_freq${freq}.mined_${mined_num}.bin"
train_file=$1
dev_file="data/conala/dev.bin"
dropout=0.3
hidden_size=256
embed_size=512
action_embed_size=128
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
batch_size=$4
max_epoch=80
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=15
#model_name=conala.${lstm}.hidden${hidden_size}.embed${embed_size}.action${action_embed_size}.field${field_embed_size}.type${type_embed_size}.dr${dropout}.lr${lr}.lr_de${lr_decay}.lr_da${lr_decay_after_epoch}.beam${beam_size}.$(basename ${vocab}).$(basename ${train_file}).glorot.par_state.seed${seed}
model_name=$3

echo "**** Writing results to logs/conala/${model_name}.log ****"
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

python exp.py \
    --cuda \
    --mode test \
    --load_model saved_models/conala/${model_name}.bin 2>&1 \
    --beam_size 15 \
    --test_file $2 \
    --evaluator conala_evaluator \
    --save_decode_to decodes/conala/$(basename $3).test.decode \
    --decode_max_time_step 100 | tee -a logs/conala/${model_name}.log
