#!/bin/bash
PYTHON_INTERPRETER="/data/cliu797/ananconda3/envs/fin-reason/bin/python"

# Verify that the Python interpreter exists and is executable
if [ ! -x "$PYTHON_INTERPRETER" ]; then
    echo "Error: Python interpreter not found or not executable at $PYTHON_INTERPRETER"
    exit 1
fi

echo "Stopping all vLLM servers..."

# Find all processes running `vllm serve` and terminate them
VLLM_PROCESSES=$(ps aux | grep "vllm serve" | grep -v grep | awk '{print $2}')

if [ -z "$VLLM_PROCESSES" ]; then
    echo "No vLLM servers are currently running."
else
    echo "Found vLLM server processes: $VLLM_PROCESSES"
    echo "$VLLM_PROCESSES" | xargs kill -9
    echo "All vLLM servers have been stopped."
fi