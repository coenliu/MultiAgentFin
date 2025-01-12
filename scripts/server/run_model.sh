#!/bin/bash
PYTHON_INTERPRETER="/data/cliu797/ananconda3/envs/fin-reason/bin/python"

# Verify that the Python interpreter exists and is executable
if [ ! -x "$PYTHON_INTERPRETER" ]; then
    echo "Error: Python interpreter not found or not executable at $PYTHON_INTERPRETER"
    exit 1
fi

# Default parameters
MODEL_NAME="meta-llama/Llama-3.2-1B-Instruct"
PORT=8002
GPU_MEMORY_UTILIZATION=0.3

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --model_name) MODEL_NAME="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        --gpu_memory_utilization) GPU_MEMORY_UTILIZATION="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Run the vLLM model server
echo "Starting the model '${MODEL_NAME}' on port ${PORT} with GPU memory utilization ${GPU_MEMORY_UTILIZATION}..."
vllm serve "$MODEL_NAME" --port "$PORT" --gpu-memory-utilization "$GPU_MEMORY_UTILIZATION"