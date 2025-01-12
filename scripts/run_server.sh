#MODEL_NAME="$1"
#autogen -n "$MODEL_NAME"
#MODEL_DIR="../megred-model-path"
#autogen -d "$MODEL_DIR"
#python -O -u -m vllm.entrypoints.openai.api_server \
#    --port=8000 \
#    --model=$HOME/models/$MODEL_NAME \
#    --tokenizer=hf-internal-testing/llama-tokenizer
#
python -m vllm.entrypoints.openai.api_server --model "megred-model-path" --port 8080 --gpu-memory-utilization 0.4 --served-model-name "llama-finetuned"
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8001 --gpu-memory-utilization 0.6
