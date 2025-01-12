# # manager.py
# import logging
# import re
# from typing import Dict, Any,  List, Tuple
# from dataclass import TaskContext
# from prompts import SYSTEM_PROMPTS
# from agents.calculation_agent import CalculationAgent
# from agents.final_output_agent import FinalOutputAgent
# from agents.reasoner import ReasonAgent
# from agents.extraction_agent import ExtractionAgent
#
#
# def camel_to_snake(name):
#     s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
#     snake_case = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
#     return snake_case
#
# class ManagerAgent:
#     name = "manager"
#
#     def __init__(
#         self,
#         config: Dict[str, Any],
#         agent_sequence: List[Tuple[str, str]],
#         args: Any,
#     ):
#         """
#         config: Loaded from YAML, containing agent_endpoints info
#         system_prompt: The manager's system instructions
#         """
#         self.config = config
#         # manager_cfg = self.config["agent_endpoints"]["manager"]
#         # self.model_name = manager_cfg["model_name"]
#         # self.vllm_endpoint = manager_cfg["endpoint"]
#
#         self.api_key = self.config.get("openai", {}).get("api_key", "")
#         self.system_prompt = SYSTEM_PROMPTS.get("manager", "manager system prompt.")
#         self.agent_sequence = agent_sequence
#         self.args = args
#         # self.llm_client = OpenAIClient(api_key=self.api_key, base_url=self.vllm_endpoint)
#
#     def run(self, context: TaskContext) -> None:
#         """
#         Orchestrate agent invocations based on the TaskContext.
#         Executes a fixed sequence: ReasonAgent -> ExtractionAgent -> CalculationAgent -> FinalOutputAgent.
#         """
#         try:
#
#             for agent_name, AgentClassName in  self.agent_sequence:
#                 logging.info(f"ManagerAgent invoking: {agent_name}")
#
#                 # Instantiate the agent
#                 AgentClass = self.get_agent_class(AgentClassName)
#                 if AgentClassName == "FinalOutputAgent":
#                     agent = AgentClass(config=self.config, output_file=self.args.output_file, output_path=self.args.output_path)
#                 else:
#                     agent = AgentClass(config=self.config)
#
#                 # Invoke the agent
#                 agent.run(context)
#
#                 # Optional: Check if Final Output Agent has completed the task
#                 if agent_name == "final_output_agent":
#                     logging.info("FinalOutputAgent invoked. Terminating ManagerAgent.")
#                     break
#
#             logging.info("ManagerAgent completed successfully.")
#
#         except Exception as e:
#             logging.error(f"Error in ManagerAgent: {e}")
#             raise
#
#     def get_agent_class(self, class_name: str):
#         """
#         Dynamically import and return the agent class based on class name.
#         """
#         try:
#             module_name = camel_to_snake(class_name)
#             module = __import__(f"agents.{module_name}", fromlist=[class_name])
#             AgentClass = getattr(module, class_name)
#             return AgentClass
#         except (ImportError, AttributeError) as e:
#             logging.error(f"Failed to import agent class '{class_name}': {e}")
#             return None