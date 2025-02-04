import csv
import json
import os
import pandas as pd
from typing import Dict, Any
from autogen_core import (
    RoutedAgent,
    type_subscription,
    MessageContext,
    message_handler
)
from dataclass import TASK_CONTEXT_MAPPING, TaskContext,output_topic_type,OutputTask
import logging
logger = logging.getLogger(__name__)
import sys
import io
import textwrap
@type_subscription(topic_type=output_topic_type)
class FormateOutput(RoutedAgent):
    def __init__(self, output_file: str, output_path: str):
        super().__init__("Formated output.")
        self.output_path = output_path
        self.output_file = output_file

    @message_handler
    async def handle_output(self, message: OutputTask, ctx: MessageContext) -> None:
        try:
            logging.info("FinalOutput started.")
            task_id = message.task_id
            task_context = TASK_CONTEXT_MAPPING[task_id]
            final_output = self.generate(task_context)
            self.save(final_output)

        except Exception as e:
            logging.error(f"Error in FinalOutputAgent: {e}")
            raise

    def generate(self, context: TaskContext) -> Dict[str, Any]:

        final_output = {
                    "task_name": context.input_data.task,
                    "context": context.input_data.context,
                    "question": context.input_data.question,
                    "answer": context.input_data.answer,
                    "program": context.input_data.program,
                    "model_output": f"{context.executor_task.get_answer()}",
                    "evaluations": "",
                    "reasoner_output": f"{context.reasoner_task.get_formula_from_reason()}",
                    "reasoner_actions":f"{context.reasoner_task.get_actions_from_reason()}",
                    "extractor_output":f"{context.extractor_task.get_extracted_var()}",
                    "executor_output": f"{context.executor_task.get_code()} \n {context.executor_task.get_answer()}",
                    "verifier_output": f"{context.verify_task.get_verify_comment()}",
                }
        return final_output

    def save(self, final_output: Dict[str, Any]) -> str:
        try:
            os.makedirs(self.output_path, exist_ok=True)
            file_path = os.path.join(self.output_path, self.output_file)
            headers = [
                "task",
                "context",
                "question",
                "answer",
                "program",
                "model_output",
                "evaluations",
                "reasoner_output",
                "reasoner_actions",
                "extractor_output",
                "executor_output",
                "verifier_output",
            ]

            if not os.path.exists(file_path):
                logger.info(f"File {file_path} does not exist. Creating a new file.")
                with open(file_path, 'w', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
            try:
                df_existing = pd.read_csv(file_path, on_bad_lines="skip")
                logger.info(f"Existing data loaded from {file_path}.")
            except pd.errors.ParserError as e:
                logger.error(f"Error reading existing CSV file: {e}")
                raise RuntimeError(f"Error reading existing CSV file: {e}") from e

            new_row = {
                "task": final_output.get("task_name", ""),
                "context": final_output.get("context", ""),
                "question": final_output.get("question", ""),
                "answer": final_output.get("answer", ""),
                "program": final_output.get("program", ""),
                "model_output": final_output.get("model_output", ""),
                "reasoner_output": final_output.get("reasoner_output", ""),
                "reasoner_actions": final_output.get("reasoner_actions", ""),
                "extractor_output": final_output.get("extractor_output", ""),
                "executor_output": final_output.get("executor_output", ""),
                "verifier_output": final_output.get("verifier_output", ""),
            }
            df_new = pd.DataFrame([new_row])

            df_combined = pd.concat([df_existing, df_new], ignore_index=True)

            df_combined.to_csv(file_path, index=False, encoding='utf-8')

            logger.info(f"Final output successfully saved to {file_path}.")
            return file_path

        except Exception as e:
            raise RuntimeError(f"Failed to save final output as CSV: {e}") from e