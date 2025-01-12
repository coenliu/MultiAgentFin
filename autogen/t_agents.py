from autogen import ConversableAgent
import autogen

local_llm_config={
    "config_list": [
        {
            "model": "meta-llama/Llama-3.2-1B-Instruct", # Same as in vLLM command
            "api_key": "NotRequired",  # Not needed
            "base_url": "http://0.0.0.0:8000/v1"  # Your vLLM URL, with '/v1' added
        }
    ],
    "cache_seed": 42, # Turns off caching, useful for testing different models
    "temperature": 0.1,
    "timeout": 300,
}

assistant = ConversableAgent("agent", llm_config=local_llm_config,system_message="Creative in software product ideas.",)


user_proxy = autogen.UserProxyAgent(
    name="User_proxy",
    system_message="A human admin.",
    code_execution_config={
        "last_n_messages": 2,
        "work_dir": "groupchat",
        "use_docker": False,
    },  # Please set use_docker=True if docker is available to run the generated code. Using docker is safer than running the generated code directly.
    human_input_mode="TERMINATE",
)
coder = autogen.AssistantAgent(
    name="Coder",
    llm_config=local_llm_config,
)
pm = autogen.AssistantAgent(
    name="Product_manager",
    system_message="Creative in software product ideas.",
    llm_config=local_llm_config,
)
groupchat = autogen.GroupChat(agents=[user_proxy, coder, pm], messages=[], max_round=12)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=local_llm_config)

user_proxy.initiate_chat(
    manager, message="Find a Nvidia stock and use python to plot it."
)