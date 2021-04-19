#!/bin/bash
set -e

seed=$5
#vocab="data/conala/vocab.src_freq3.code_freq3.mined_100000.snippet5.bin"
vocab=$1
dev_file="data/conala/dev.bin"
test_file=$2
dev_decode_file=$3".dev.bin.decode"
test_decode_file=$3".test.decode"
reranker_file=$4".bin"
paraphrase_file=$4".bin.paraphrase_identifier"
reconstructor_file=$4".bin.reconstructor"
dropout=0.3
hidden_size=256
embed_size=512
action_embed_size=512
field_embed_size=64
type_embed_size=64
lr=0.001
lr_decay=0.5
batch_size=16
max_epoch=80
beam_size=15
lstm='lstm'  # lstm
lr_decay_after_epoch=15
num_workers=70
model_name=reranker.conala.$3

echo "**** Writing results to logs/conala/${model_name}.log ****"
mkdir -p logs/conala
echo commit hash: `git rev-parse HEAD` > logs/conala/${model_name}.log

python -u exp.py \
    --cuda \
    --seed ${seed} \
    --mode rerank \
    --batch_size ${batch_size} \
    --evaluator conala_evaluator \
    --asdl_file asdl/lang/py3/py3_asdl.simplified.txt \
    --parser python3 \
    --load_reranker ${reranker_file} \
    --load_reconstruction_model ${reconstructor_file} \
    --load_paraphrase_model ${paraphrase_file} \
    --save_decode_to decodes/conala/${model_name}.best \
    --dev_file ${dev_file} \
    --test_file ${test_file} \
    --dev_decode_file decodes/conala/${dev_decode_file} \
    --test_decode_file decodes/conala/${test_decode_file} \
    --vocab ${vocab} \
    --features word_cnt parser_score \
    --lstm ${lstm} \
    --num_workers ${num_workers} \
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

