

```run bash file```
chmod +x ./scripts/test.sh
./scripts/test.sh

chmod +x ./scripts/reason.sh
./scripts/reason.sh

chmod +x ./scripts/server/run_model.sh
./scripts/server/run_model.sh

chmod +x ./scripts/server/run_2.sh
./scripts/server/run_2.sh

chmod +x ./scripts/reason_finetuned.sh
./scripts/reason_finetuned.sh



~~## Manager on 8003
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8003 &
vllm serve meta-llama/Meta-Llama-3-8B-Instruct --port 8003 --gpu-memory-utilization 0.5~~
## Reasoning on 8000
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8000 --gpu-memory-utilization 0.5 &
vllm serve meta-llama/Meta-Llama-3-8B-Instruct --port 8000 --gpu-memory-utilization 0.4

python -m vllm.entrypoints.openai.api_server --model "megred-model-path" --port 8080 --gpu-memory-utilization 0.4 --served-model-name "llama-finetuned"
## Extraction on 8001
vllm --model /path/to/extraction_model --port 8001 &
vllm serve meta-llama/Llama-3.2-3B-Instruct --port 8001 --gpu-memory-utilization 0.4
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8001 --gpu-memory-utilization 0.6
## Calculation on 8002 #should in the same gpu with reason agent
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8002 &
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8002 --gpu-memory-utilization 0.5 
vllm serve meta-llama/Meta-Llama-3-8B-Instruct --port 8002 --gpu-memory-utilization 0.5
## Final on 8004 if needed
vllm --model /path/to/final_output_model --port 8004 &

## Verify:
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8004 --gpu-memory-utilization 0.5 

```auto gen```
vllm serve meta-llama/Llama-3.2-1B-Instruct --port 8000 --chat-template tool_chat_template_llama3.2_json.jinja

```CUDA```
export CUDA_VISIBLE_DEVICES=4
export PIP_CACHE_DIR=/data/cliu797/tmp/pip_cache
```cache```
export HF_HOME=/data/cliu797/project/cache
export TRANSFORMERS_CACHE=/data/cliu797/project/cache
export TORCH_HOME=/data/cliu797/project/cache

```upload to cluster 2 ```
 export PATH=/data/cliu797/ananconda3/envs/fin-reason/bin:$PATH

scp -r MultiAgentFin cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project
scp -r scripts cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin
scp -r agents cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin
scp -r configs cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin

scp configs/config.yaml cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin/configs
scp manager.py cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin
scp main.py cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin
scp prompts.py cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin

```download from cluster 2```
scp cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin/results/fincode/Test_fincode_llama3.2_1B_full.csv results/test
scp cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin/results/codetat/Test_codetat_agent_full.csv results/test

scp -r cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/MultiAgentFin/results ./
scp -r cliu797@foscsmlprd02.its.auckland.ac.nz:/data/cliu797/project/LLaMA-Factory/megred-model-path ./


```curl```
curl http://localhost:8003/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "meta-llama/Meta-Llama-3-8B-Instruct", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Who won the world series in 2020?"}]}'
curl -X POST http://127.0.0.1:8002/v1/chat/completions -H "Content-Type: application/json" -d '{"model": "meta-llama/Llama-3.2-1B-Instruct", "messages": [{"role": "system", "content": "Hello"}]}'
curl --max-time 10 --connect-timeout 5 http://localhost:8080/v1/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -d '{
           "model": "llama-finetuned",
           "prompt": "What is the formula for calculating the percentage decrease in potential maximum exposure by the end of 2012?",
           "max_tokens": 50,
           "temperature": 0.7
         }'