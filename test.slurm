#!/bin/bash

# Nombre de machine ou NODES typiquement=1 sauf
#SBATCH -N 1

# Nombre de processus en general=1 (a mémoire distribues type miprun)
#SBATCH --ntasks=1

#SBATCH --gres=gpu:1

# Nom de votre job afficher dans la lise par squeue
#SBATCH --job-name=external_knowledge_codegen_train

# Nom du fichier de sortie et des erreurs avec l'id du job
#SBATCH --output=res_%j.log
#####SBATCH --error=res_%j.err

#SBATCH --partition=gpu

# Mail pour etre informe de l'etat de votre job
#SBATCH --mail-type=start,end,fail
#SBATCH --mail-user=gael.de-chalendar@cea.fr

# Temps maximal d'execution du job ci dessous
# d-hh:mm:ss
#SBATCH --time=7-0:00:00

# Taille de la memoire exprime en Mega octets max=190000 ici 50G
#SBATCH --mem=50G

#SBATCH --exclude=node5
####SBATCH --nodelist=node6,node7

#set -o nounset
set -o errexit
set -o pipefail

echo "$0"

# activate environments
source /home/gael/miniconda3/bin/activate
source activate tranx

/usr/bin/env python3 --version
if [[ -v SLURM_JOB_ID ]] ; then
  nvidia-smi

  # Affiche la (ou les gpus) allouee par Slurm pour ce job
  echo "CUDA_VISIBLE_DEVICES: $CUDA_VISIBLE_DEVICES"
fi

echo "Begin on machine: `hostname`"

# conda list

EXECUTOR=srun
if [ -z ${SLURM_JOB_ID+x} ]; then
  echo "Not in sbatch"
  EXECUTOR=
fi
echo "EXECUTOR is ${EXECUTOR}"


##############

echo 'Script starting'

cd /home/gael/Projets/Decoder/external-knowledge-codegen

# run script
echo "Testing authors' best"
${EXECUTOR} scripts/conala/test.sh best_pretrained_models/finetune.mined.retapi.distsmpl.dr0.3.lr0.001.lr_de0.5.lr_da15.beam15.seed0.mined_100000.intent_count100k_topk1_temp5.bin

echo 'Testing our best'
${EXECUTOR} scripts/conala/test.sh saved_models/conala/20210303/finetune.mined.retapi.distsmpl.dr0.3.lr0.001.lr_de0.5.lr_da15.beam15.seed0.mined_100000.snippet_count100k_topk1_temp2.bin

wait

echo "Slurm script Done."

