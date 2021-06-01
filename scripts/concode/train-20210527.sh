#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

seed=0
vocab="data/concode/20210527/vocab.src_freq3.code_freq3"
train_file="data/concode/20210527/train.all_0.bin"
dev_file="data/concode/20210527/dev.bin"
dropout=0.3
hidden_size=256
embed_size=128
action_embed_size=128
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
batch_size=32
max_epoch=80
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=15
model_name=concode.${lstm}.hidden${hidden_size}.embed${embed_size}.action${action_embed_size}.field${field_embed_size}.type${type_embed_size}.dr${dropout}.lr${lr}.lr_de${lr_decay}.lr_da${lr_decay_after_epoch}.beam${beam_size}.$(basename ${vocab}).$(basename ${train_file}).glorot.par_state.seed${seed}

echo "**** Writing results to logs/concode/${model_name}.log ****"
mkdir -p logs/concode
echo commit hash: `git rev-parse HEAD` > logs/concode/${model_name}.log

#     --cuda \
python -u exp.py \
    --lang java \
    --seed ${seed} \
    --mode train \
    --batch_size ${batch_size} \
    --evaluator concode_evaluator \
    --asdl_file asdl/lang/java/java_asdl.simplified.txt \
    --transition_system java \
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
    --save_to saved_models/concode/${model_name} \
    --save_decode_to decodes/concode/${model_name}.decode \
    --root_production "typedeclaration,MethodDeclaration" 2>&1 | tee logs/concode/${model_name}.log

. scripts/concode/test.sh saved_models/concode/${model_name}.bin 2>&1 | tee -a logs/concode/${model_name}.log
