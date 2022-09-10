#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

export PYTHONPATH=${SCRIPT_DIR}:${PYTHONPATH}

LLVM_VERSION=15
export PATH=/home/gael/Logiciels/llvm-${LLVM_VERSION}/bin:$PATH
export LD_LIBRARY_PATH=/home/gael/Logiciels/llvm-${LLVM_VERSION}/lib:$LD_LIBRARY_PATH

