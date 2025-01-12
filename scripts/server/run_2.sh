#!/bin/bash

# Default parameters
GPU_MEMORY_UTILIZATION=0.3

# Model names and their corresponding ports
declare -A MODEL_PORTS=(
    ["meta-llama/Llama-3.2-1B-Instruct"]=8000
    ["meta-llama/Llama-3.2-1B-Instruct"]=8001
    ["meta-llama/Llama-3.2-1B-Instruct"]=8002
)

# Loop over the model names and run the vLLM model server for each
for MODEL_NAME in "${!MODEL_PORTS[@]}"; do
    PORT=${MODEL_PORTS[$MODEL_NAME]}
    echo "Starting the model '${MODEL_NAME}' on port ${PORT} with GPU memory utilization ${GPU_MEMORY_UTILIZATION}..."
    vllm serve "$MODEL_NAME" --port "$PORT" --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"
done