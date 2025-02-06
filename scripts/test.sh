#export PYTHONPATH=/Users/chenghao/Work/Code/FinReason:$PYTHONPATH
export PYTHONPATH=/home/chenghao/anaconda3/envs/MultiAgentFin:$PYTHONPATH
#export PYTHONPATH=/data/cliu797/project/FinReason:$PYTHONPATH
export DISKCACHE_PATH=/data/cliu797/diskcache
export no_proxy=127.0.0.1,localhost


#PIPELINE="reason"
DATA_PATH="data/bizBench/test-00000-of-00001-7b139510152259c8.parquet"  # Update with the actual Parquet file path
FEW_SHOT=0  # Update as needed for the number of few-shot examples
TOP_N=15 # Update as needed to limit the number of samples
DATASET_NAME="CodeTAT-QA" #CodeFinQA,FinCode,  CodeTAT-QA, TAT-QA,  SEC-NUM,ConvFinQA,
CONFIG_FILE="configs/config.yaml"
OUTPUT_PATH="results/test/test_100"  # Update the output path for results
OUTPUT_FILE="Test_rollout20_Action_CodeTAT-QA_code13B_coro_full.csv" #
LLM_GPU_MEMORY_UTILIZATION=0.9  # Update as needed
LLM_MAX_TOKENS=8000  # Before upload to cluster
TEMPERATURE=0.1  # Update as needed

# Run the main script
#python main.py \
#  --data_path $DATA_PATH \
#  --top_n $TOP_N \
#  --dataset_name $DATASET_NAME \
#  --output_path $OUTPUT_PATH \
#  --output_file $OUTPUT_FILE \
#  --temperature $TEMPERATURE

#full example
python main.py \
  --data_path $DATA_PATH \
  --dataset_name $DATASET_NAME \
  --output_path $OUTPUT_PATH \
  --output_file $OUTPUT_FILE \
  --temperature $TEMPERATURE