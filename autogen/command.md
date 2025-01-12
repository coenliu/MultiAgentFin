python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.2-1B-Instruct --port 8000 --chat-template autogen/tool_chat_template_llama3.2_json.jinja

python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.2-1B-Instruct --port 8000 --chat-template autogen/tool_chat_template_llama3.2_pythonic.jinja
python -m vllm.entrypoints.openai.api_server --model meta-llama/Llama-3.2-1B-Instruct --port 8000 --gpu_memory_utilization 0.9 --chat-template autogen/tool_chat_template_llama3.2_pythonic.jinja

