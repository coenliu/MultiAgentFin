import asyncio
import uuid
import tqdm
from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
)
from agents.reasoner import ReasonerAgent
from agents.executor import ExecutorAgent
from agents.extractor import ExtractorAgent
from agents.verifier import VerifierAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dataclass import TASK_CONTEXT_MAPPING, reasoner_topic_type, executor_topic_type, extractor_topic_type,verifier_topic_type, ReasonTask, TaskContext, output_topic_type
import argparse
import logging
from dataloader.parquet_dataset import ParquetDataset, load_parquet
from dataloader.utils import dataset_to_task_inputs, inputs_to_contexts
from agents.formate_output import FormateOutput
from typing import Any, List,Dict
model_client = OpenAIChatCompletionClient(
    model="meta-llama/Llama-3.2-1B-Instruct",
    base_url="http://0.0.0.0:8000/v1",
    api_key="placeholder",
    temperature=0.1,
    top_p=0.9,
    max_tokens=500,
    model_capabilities={
        "vision": False,
        "function_calling": True,
        "json_output": True,
    },
)


AGENT_SEQUENCES = {
    "default": [
        ("reason_agent", "ReasonAgent"),
        ("extract_agent", "ExtractionAgent"),
        ("executor_agent", "ExecutorAgent"),
        ("verifier_agent", "VerifyAgent"),
        ("formate_output", "FormateOutput"),
    ],
    # "no_reason": [
    #     ("extract_agent", "ExtractionAgent"),
    #     ("calculation_agent", "CalculationAgent"),
    #     ("final_output_agent", "FinalOutputAgent"),
    # ],
    # "no_extract": [
    #     ("reason_agent", "ReasonAgent"),
    #     ("calculation_agent", "CalculationAgent"),
    #     ("final_output_agent", "FinalOutputAgent"),
    # ],
    # "no_reason_extract": [
    #     ("calculation_agent", "CalculationAgent"),
    #     ("final_output_agent", "FinalOutputAgent"),
    # ],
}

def load_and_prepare_dataset(
    data_path: str, task_name: str, top_n: int
) -> ParquetDataset:

    df = load_parquet(data_path)
    dataset = ParquetDataset(df)
    dataset = dataset.filter_by_task(task_name)

    if top_n is not None:
        dataset = dataset.select_top_n(top_n)
        logging.info(f"Processing only the top {top_n} samples.")

    if len(dataset) == 0:
        exit(0)

    return dataset

def parse_args():
    parser = argparse.ArgumentParser(description="Run multi-agent system with Manager Agent. No pipeline.")
    parser.add_argument('--top_n', type=int, default=None, help="Limit the number of top samples to process (e.g., top 10)")
    parser.add_argument("--sequence", type=str, choices=AGENT_SEQUENCES.keys(), default="default", help="Choose the agent sequence to execute.")
    parser.add_argument('--dataset_name', type=str, default=None, help="CodeFinQA")
    parser.add_argument("--data_path", type=str, required=True, help="Path to Parquet data.")
    parser.add_argument("--output_path", type=str, default="", help="Output path for task results.")
    parser.add_argument('--output_file', type=str, default="llama_outputs.csv", help="Name to the output CSV file")
    parser.add_argument('--temperature', type=float, default=0.3, help="Temperature for text generation")
    return parser.parse_args()

async def register_agents(runtime: SingleThreadedAgentRuntime, agent_sequence: List[str], output_path: str, output_file: str):
    """
    Registers agents with the runtime based on the agent sequence.

    Args:
        runtime (SingleThreadedAgentRuntime): The agent runtime.
        agent_sequence (List[str]): List of agent names to register.
        output_path (str): Directory path for FormateOutput .
        output_file (str): Filename for FormateOutput .
    """
    agents_to_register = [agent[0] for agent in AGENT_SEQUENCES[agent_sequence]]

    if "reason_agent" in agents_to_register:
        await ReasonerAgent.register(
            runtime,
            type=reasoner_topic_type,
            factory=lambda: ReasonerAgent(model_client=model_client)  # task_context handled via messages
        )

    if "extract_agent" in agents_to_register:
        await ExtractorAgent.register(
            runtime,
            type=extractor_topic_type,
            factory=lambda: ExtractorAgent(model_client=model_client)
        )

    if "executor_agent" in agents_to_register:
        await ExecutorAgent.register(
            runtime,
            type=executor_topic_type,
            factory=lambda: ExecutorAgent(model_client=model_client)
        )

    if "verifier_agent" in agents_to_register:
        await VerifierAgent.register(
            runtime,
            type=verifier_topic_type,
            factory=lambda: VerifierAgent(model_client=model_client)
        )

    if "formate_output" in agents_to_register:
        await FormateOutput.register(
            runtime,
            type=output_topic_type,
            factory=lambda: FormateOutput(output_path=output_path, output_file=output_file)
        )

async def publish_tasks(runtime: SingleThreadedAgentRuntime, task_contexts: List[TaskContext]):
    """
    Publishes tasks to the runtime for processing.
    """
    for idx, ctx in (enumerate(task_contexts, start=1)):
        task_id = str(uuid.uuid4())
        TASK_CONTEXT_MAPPING[task_id] = ctx
        await runtime.publish_message(
            ReasonTask(task="", task_id=task_id),
            topic_id=TopicId(reasoner_topic_type, source="default"),
        )

async def main(args):
    """
    The main asynchronous function to process all task contexts.
    """
    agent_sequence = args.sequence
    dataset = load_and_prepare_dataset(
        data_path=args.data_path,
        task_name=args.dataset_name,
        top_n=args.top_n
    )
    output_file = args.output_file
    output_path = args.output_path
    task_inputs = dataset_to_task_inputs(dataset=dataset)

    task_contexts = inputs_to_contexts(task_inputs)

    runtime = SingleThreadedAgentRuntime()
    await register_agents(runtime, agent_sequence, output_path, output_file)
    runtime.start()
    await publish_tasks(runtime, task_contexts)
    await runtime.stop_when_idle()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(args))

