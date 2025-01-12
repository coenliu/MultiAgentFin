#!/bin/bash

# Export necessary environment variables
export PYTHONPATH=/data/cliu797/project/FinReason:$PYTHONPATH
export DISKCACHE_PATH=/data/cliu797/diskcache
export no_proxy=127.0.0.1,localhost

# Define an array of dataset names
DATASET_NAMES=("CodeFinQA" "FinCode" "CodeTAT-QA")

# Common variables (if any) can be defined here
DATA_PATH="data/bizBench/test-00000-of-00001-7b139510152259c8.parquet"  # Update if different per dataset
FEW_SHOT=0  # Update as needed for the number of few-shot examples
TOP_N=1  # Update as needed to limit the number of samples
CONFIG_FILE="configs/config.yaml"
LLM_GPU_MEMORY_UTILIZATION=0.9  # Update as needed
LLM_MAX_TOKENS=8000  # Before upload to cluster
TEMPERATURE=0.1  # Update as needed

# Loop over each dataset name
for DATASET_NAME in "${DATASET_NAMES[@]}"; do
    echo "Processing dataset: $DATASET_NAME"
    OUTPUT_DIR="results/$(echo "$DATASET_NAME" | tr '[:upper:]' '[:lower:]')"
    OUTPUT_PATH="$OUTPUT_DIR"  # Update the output path for results
    OUTPUT_FILE="Test_${DATASET_NAME}_agent_full_llama3.csv"  # e.g., Test_CodeFinQA_agent_full.csv

    # Create the output directory if it doesn't exist
    mkdir -p "$OUTPUT_PATH"

    # Execute the Python script with the specified parameters
    python main.py \
      --data_path "$DATA_PATH" \
      --dataset_name "$DATASET_NAME" \
      --config_file "$CONFIG_FILE" \
      --output_path "$OUTPUT_PATH" \
      --output_file "$OUTPUT_FILE" \
      --temperature "$TEMPERATURE"

    # Optional: Add a separator for readability in logs
    echo "Completed processing for dataset: $DATASET_NAME"
    echo "---------------------------------------------"

done

echo "All datasets have been processed."