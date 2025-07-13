#!/usr/bin/env bash
set -e
MODEL_DIR=/models
mkdir -p $MODEL_DIR
cd /llama
huggingface-cli download meta-llama/Meta-Llama-3-8B-Instruct \
  --include "pytorch_model-00001-of-00002.safetensors,*.json" --local-dir $MODEL_DIR
python3 convert.py --outfile $MODEL_DIR/llama3-f16.gguf --outtype f16 $MODEL_DIR
./quantize $MODEL_DIR/llama3-f16.gguf $MODEL_DIR/llama3-q4_K_M.gguf q4_K_M
