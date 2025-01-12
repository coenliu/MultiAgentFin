import asyncio
from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
)
from agents.reasoner import ReasonerAgent
from agents.executor import ExecutorAgent
from agents.extractor import ExtractorAgent
from agents.verifier import VerifierAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dataclass import reasoner_topic_type, executor_topic_type, extractor_topic_type,verifier_topic_type, ReasonTask, TaskContext

model_client = OpenAIChatCompletionClient(
    model="meta-llama/Llama-3.2-1B-Instruct",
    base_url="http://0.0.0.0:8000/v1",
    api_key="placeholder",
    model_capabilities={
        "vision": False,
        "function_calling": True,
        "json_output": True,
    },
)


async def main():
    task_context = TaskContext()
    runtime = SingleThreadedAgentRuntime()
    await ReasonerAgent.register(runtime, type=reasoner_topic_type, factory=lambda: ReasonerAgent(model_client=model_client, task_context=task_context))
    await ExtractorAgent.register(runtime, type= extractor_topic_type,factory=lambda: ExtractorAgent(model_client=model_client, task_context=task_context))
    await ExecutorAgent.register(runtime, type= executor_topic_type,factory=lambda: ExecutorAgent(model_client=model_client, task_context=task_context))
    await VerifierAgent.register(runtime, type= verifier_topic_type,factory=lambda: VerifierAgent(model_client=model_client, task_context=task_context))
    runtime.start()
    await runtime.publish_message(
        ReasonTask(task="""The goldman sachs group , inc . and subsidiaries notes to consolidated financial statements the firm is unable to develop an estimate of the maximum payout under these guarantees and indemnifications . 
        however , management believes that it is unlikely the firm will have to make any material payments under these arrangements , 
        and no material liabilities related to these guarantees and indemnifications have been recognized in the consolidated statements of financial condition as of both december 2017 and december 2016 . other representations , warranties and indemnifications . 
        the firm provides representations and warranties to counterparties in connection with a variety of commercial transactions and occasionally indemnifies them against potential losses caused by the breach of those representations and warranties . 
        the firm may also provide indemnifications protecting against changes in or adverse application of certain u.s . 
        tax laws in connection with ordinary-course transactions such as securities issuances , borrowings or derivatives . 
        in addition , the firm may provide indemnifications to some counterparties to protect them in the event additional taxes are owed or payments are withheld , due either to a change in or an adverse application of certain non-u.s . tax laws . these indemnifications generally are standard contractual terms and are entered into in the ordinary course of business . generally , there are no stated or notional amounts included in these indemnifications , and the contingencies triggering the obligation to indemnify are not expected to occur . 
        the firm is unable to develop an estimate of the maximum payout under these guarantees and indemnifications . however , management believes that it is unlikely the firm will have to make any material payments under these arrangements , and no material liabilities related to these arrangements have been recognized in the consolidated statements of financial condition as of both december 2017 and december 2016 . guarantees of subsidiaries . group inc . fully and unconditionally guarantees the securities issued by gs finance corp. , a wholly-owned finance subsidiary of the firm . group inc . has guaranteed the payment obligations of goldman sachs & co . llc ( gs&co. ) and gs bank usa , subject to certain exceptions .
         in addition , group inc . guarantees many of the obligations of its other consolidated subsidiaries on a transaction-by-transaction basis , as negotiated with counterparties . group inc . is unable to develop an estimate of the maximum payout under its subsidiary guarantees ; however , because these guaranteed obligations are also obligations of consolidated subsidiaries , group inc . 2019s liabilities as guarantor are not separately disclosed . note 19 . shareholders 2019 equity common equity as of both december 2017 and december 2016 , 
         the firm had 4.00 billion authorized shares of common stock and 200 million authorized shares of nonvoting common stock , each with a par value of $ 0.01 per share . dividends declared per common share were $ 2.90 in 2017 , $ 2.60 in 2016 and $ 2.55 in 2015 . on january 16 , 2018 , the board of directors of group inc . ( board ) declared a dividend of $ 0.75 per common share to be paid on march 29 , 2018 to common shareholders of record on march 1 , 2018 . the firm 2019s share repurchase program is intended to help maintain the appropriate level of common equity . the share repurchase program is effected primarily through regular open-market purchases 
         ( which may include repurchase plans designed to comply with rule 10b5-1 ) , the amounts and timing of which are determined primarily by the firm 2019s current and projected capital position , but which may also be influenced by general market conditions and the prevailing price and trading volumes of the firm 2019s common stock . prior to repurchasing common stock , the firm must receive confirmation that the frb does not object to such capital action . the table below presents the amount of common stock repurchased by the firm under the share repurchase program. 
         |  | Year Ended December |
        | :--- | :--- |
        | <i>in millions, except per share amounts</i> | 2017 | 2016 | 2015 |
        | Common share repurchases | 29.0 | 36.6 | 22.1 |
        | Average cost per share | $231.87 | $165.88 | $189.41 |
        | Total cost of common share repurchases | $ 6,721 | $ 6,069 | $ 4,195 |
        pursuant to the terms of certain share-based compensation plans , employees may remit shares to the firm or the firm may cancel rsus or stock options to satisfy minimum statutory employee tax withholding requirements and the exercise price of stock options . under these plans , during 2017 , 2016 and 2015 , 12165 shares , 49374 shares and 35217 shares were remitted with a total value of $ 3 million , $ 7 million and $ 6 million , and the firm cancelled 8.1 million , 6.1 million and 5.7 million of rsus with a total value of $ 1.94 billion , $ 921 million and $ 1.03 billion , respectively . under these plans , the firm also cancelled 4.6 million , 5.5 million and 2.0 million of stock options with a total value of $ 1.09 billion , $ 1.11 billion and $ 406 million during 2017 , 2016 and 2015 , respectively . 166 goldman sachs 2017 form 10-k .
         Question: what is the total amount of stock options cancelled in millions during 2017 , 2016 and 2015?
         """),
        topic_id=TopicId(reasoner_topic_type, source="default"),
    )
    await runtime.stop_when_idle()



asyncio.run(main())
# # main.py
#
# import argparse
# import logging
# import json
# from typing import List
#
# from dataclass import TaskInput, TaskContext
# from manager import ManagerAgent
# from utils import setup_logger, load_config, load_parquet
# from dataloader.parquet_dataset import ParquetDataset
# from dataloader.utils import dataset_to_task_inputs, inputs_to_contexts
#
# AGENT_SEQUENCES = {
#     "default": [
#         ("reason_agent", "ReasonAgent"),
#         ("extract_agent", "ExtractionAgent"),
#         ("verify_agent", "VerifyAgent"),
#         # ("tool_agent", "ToolAgent"),
#         # ("calculation_agent", "CalculationAgent"),
#         ("final_output_agent", "FinalOutputAgent"),
#     ],
#     "no_reason": [
#         ("extract_agent", "ExtractionAgent"),
#         ("calculation_agent", "CalculationAgent"),
#         ("final_output_agent", "FinalOutputAgent"),
#     ],
#     "no_extract": [
#         ("reason_agent", "ReasonAgent"),
#         ("calculation_agent", "CalculationAgent"),
#         ("final_output_agent", "FinalOutputAgent"),
#     ],
#     "no_reason_extract": [
#         ("calculation_agent", "CalculationAgent"),
#         ("final_output_agent", "FinalOutputAgent"),
#     ],
# }
#
# def parse_args():
#     parser = argparse.ArgumentParser(description="Run multi-agent system with Manager Agent. No pipeline.")
#     parser.add_argument('--top_n', type=int, default=None, help="Limit the number of top samples to process (e.g., top 10)")
#     parser.add_argument("--sequence", type=str, choices=AGENT_SEQUENCES.keys(), default="default", help="Choose the agent sequence to execute.")
#     parser.add_argument('--dataset_name', type=str, default=None, help="CodeFinQA")
#     parser.add_argument("--config_file", type=str, default="configs/config.yaml", help="Path to config YAML.")
#     parser.add_argument("--data_path", type=str, required=True, help="Path to Parquet data.")
#     parser.add_argument("--output_path", type=str, default="", help="Output path for task results.")
#     parser.add_argument('--output_file', type=str, default="llama_outputs.csv", help="Name to the output CSV file")
#     parser.add_argument('--temperature', type=float, default=0.3, help="Temperature for text generation")
#     return parser.parse_args()
#
#
#
# def load_and_prepare_dataset(
#     data_path: str, task_name: str, top_n: int
# ) -> ParquetDataset:
#
#     df = load_parquet(data_path)
#     dataset = ParquetDataset(df)
#     dataset = dataset.filter_by_task(task_name)
#
#     if top_n is not None:
#         dataset = dataset.select_top_n(top_n)
#         logging.info(f"Processing only the top {top_n} samples.")
#
#     if len(dataset) == 0:
#         logging.warning(f"No samples found for task '{task_name}'.")
#         exit(0)
#
#     return dataset
#
#
# def main():
#     args = parse_args()
#     config = load_config(args.config_file)
#     setup_logger(
#         log_level=config.get("logging",{}).get("level","INFO"),
#         log_file=config.get("logging",{}).get("file","logs/app.log")
#     )
#
#     dataset = load_and_prepare_dataset(data_path=args.data_path, task_name=args.dataset_name, top_n=args.top_n)
#
#     task_inputs = dataset_to_task_inputs(dataset = dataset)
#
#     selected_sequence = AGENT_SEQUENCES.get(args.sequence)
#     if not selected_sequence:
#         logging.error(f"Invalid agent sequence selected: {args.sequence}")
#         return
#
#     task_contexts = Optional[(task_inputs)  # Convert TaskInputs to TaskContexts
#
#     manager = ManagerAgent(
#         config=config,
#         agent_sequence=selected_sequence,
#         args=args
#     )
#
#     # Manager orchestrates for each context
#     for ctx in task_contexts:
#         manager.run(ctx)
#
#     logging.info("All contexts processed successfully.")
#
# if __name__ == "__main__":
#     main()