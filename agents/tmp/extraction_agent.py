# extraction_agent.py

import logging
from dataclass import TaskContext, ModuleResult
from agents.tmp.llm_interface import OpenAIClient
from prompts import SYSTEM_PROMPTS

class ExtractionAgent:
    name = "extraction"

    def __init__(self, config):
        self.config = config
        extr_cfg = self.config["agent_endpoints"]["extraction"]
        self.model_name = extr_cfg["model_name"]
        self.vllm_endpoint = extr_cfg["endpoint"]
        self.api_key = self.config.get("openai", {}).get("api_key","")

        self.system_prompt = SYSTEM_PROMPTS.get("extraction", "Extract system prompt.")
        self.llm_client = OpenAIClient(api_key=self.api_key, base_url=self.vllm_endpoint)

    def run(self, context: TaskContext) -> None:
        try:
            logging.info("ExtractionAgent started.")

            reason_response = context.intermediate_data.get("reasoning", "")

            msgs = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Data: {context.input_data.context}"},
                {"role": "user", "content": f"Question: {context.input_data.question}"},
            ]

            if reason_response:
                logging.info("Reason Agent's response found. Adding to messages.")
                msgs.append({"role": "assistant", "content": f"Here is a general guidance {reason_response}"})

            response = self.llm_client.generate_response(
                messages=msgs,
                model=self.model_name,
                max_tokens=512,
                temperature=0.3,
                top_p=0.9,
                seed=42
            )

            print(f"response from extract = {response}")


            mod_res = ModuleResult(
                module_name=self.name,
                output_data={"Extraction": response},
                success=True
            )
            context.add_module_result(self.name, mod_res)
            context.update_intermediate_data(key=self.name, value=response)
            context.add_message_to_conversation(role="assistant", content=response)


            logging.info("ExtractionAgent complete.")
        except Exception as e:
            raise RuntimeError(f"ExtractionAgent failed: {e}")