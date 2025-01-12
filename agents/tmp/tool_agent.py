from dataclass import TaskContext
from agents.tmp.llm_interface import OpenAIClient
from prompts import SYSTEM_PROMPTS

class ToolAgent:
    name = "tool"

    def __init__(self, config):
        self.config = config
        tool_cfg = self.config["agent_endpoints"]["tool"]
        self.model_name = tool_cfg["model_name"]
        self.vllm_endpoint = tool_cfg["endpoint"]
        self.api_key = self.config.get("openai", {}).get("api_key", "")

        self.system_prompt = SYSTEM_PROMPTS.get("tool", "tool system prompt.")
        self.llm_client = OpenAIClient(api_key=self.api_key, base_url=self.vllm_endpoint)

        def run(self, context: TaskContext) -> None:
            pass

# import tempfile
#
# from autogen import ConversableAgent
# from autogen.coding import LocalCommandLineCodeExecutor
#
# # Create a temporary directory to store the code files.
# temp_dir = tempfile.TemporaryDirectory()
#
# # Create a local command line code executor.
# executor = LocalCommandLineCodeExecutor(
#     timeout=10,  # Timeout for each code execution in seconds.
#     work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
# )
#
# # Create an agent with code executor configuration.
# code_executor_agent = ConversableAgent(
#     "code_executor_agent",
#     llm_config=False,  # Turn off LLM for this agent.
#     code_execution_config={"executor": executor},  # Use the local command line code executor.
#     human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
# )
#
# message_with_code_block = """This is a message with code block.
# The code block is below:
# ```python
# import numpy as np
# import matplotlib.pyplot as plt
# x = np.random.randint(0, 100, 100)
# y = np.random.randint(0, 100, 100)
# plt.scatter(x, y)
# plt.savefig('scatter.png')
# print('Scatter plot saved to scatter.png')
# ```
#
# This is the end of the message.
# """
#
# # Generate a reply for the given code.
# reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": message_with_code_block}])
# print(reply)