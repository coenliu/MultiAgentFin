# calculation_agent.py

import logging
from dataclass import TaskContext, ModuleResult
from agents.tmp.llm_interface import OpenAIClient
from prompts import SYSTEM_PROMPTS

class CalculationAgent:
    name = "calculation"

    def __init__(self, config):
        self.config = config
        calc_cfg = self.config["agent_endpoints"]["calculation"]
        self.model_name = calc_cfg["model_name"]
        self.vllm_endpoint = calc_cfg["endpoint"]
        self.api_key = self.config.get("openai", {}).get("api_key","")

        self.system_prompt = SYSTEM_PROMPTS.get("calculation", "Calculation system prompt.")
        self.llm_client = OpenAIClient(api_key=self.api_key, base_url=self.vllm_endpoint)

    def run(self, context: TaskContext) -> None:
        try:
            logging.info("CalculationAgent started.")

            reason_response = context.intermediate_data.get("reasoning", "")
            extract_response = context.intermediate_data.get("extraction", "")

            msgs = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Q: {context.input_data.question}"},
                # {"role": "user", "content": f"Data: {context.input_data.context}"}
            ]

            if reason_response:
                logging.info("Reason Agent's response found. Adding to messages.")
                msgs.append({"role": "assistant", "content": f"Here is a formula {reason_response}"})

            if extract_response:
                msgs.append({"role": "assistant", "content": f"Here is a extracted numerical data {extract_response}"})

            print(f"this is input to calculation: {msgs}")

            response = self.llm_client.generate_response(
                messages=msgs,
                model=self.model_name,
                max_tokens=512,
                temperature=0.3,
                top_p=0.9,
                seed=42
            )

            print(f"response from calculation agent: {response}")


            mod_res = ModuleResult(
                module_name=self.name,
                output_data={self.name: response},
                success=True
            )
            context.add_module_result(self.name, mod_res)
            context.update_intermediate_data(key=self.name, value=response)
            context.add_message_to_conversation(role="assistant", content=response)

            logging.info("CalculationAgent complete.")
        except Exception as e:
            raise RuntimeError(f"CalculationAgent failed: {e}")