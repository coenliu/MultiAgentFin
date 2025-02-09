import json
import logging

from pandas import DataFrame

from dataclass import TaskInput, TaskContext
from .parquet_dataset import ParquetDataset
from typing import List
import pandas as pd
from .finmath import FinMathDataset

task_dict = {
    "fincode_code.json": "FinCode",
    "fincode_cot.json": "FinCode",
    "tatqa_e.json": "TAT-QA",
    "finknow.json": "FinKnow",
    "codefinqa_code.json": "CodeFinQA",
    "codefinqa_cot.json": "CodeFinQA",
    "codetatqa_code.json": "CodeTAT-QA",
    "codetatqa_cot.json": "CodeTAT-QA",
    "secnum_e.json": "SEC-NUM",
    "convfinqa_e.json": "ConvFinQA",
    "FormulaEval":"FormulaEval",
    "convfinqa.json":"ConvFinQA"
}
logging.basicConfig(level=logging.INFO)

def load_system_message(json_file_path):
    """
    Loads the system message from a JSON file.
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    system_message = data.get('system_message', 'No system message provided.')
    return system_message

def dataset_to_task_inputs(dataset: ParquetDataset) -> List[TaskInput]:
    """
    Converts a ParquetDataset into a list of TaskInput objects.
    """
    task_inputs = []

    for idx, row in dataset.data.iterrows():
        try:
            task_input = TaskInput(
                question=row.get("question", ""),
                answer=row.get("answer", None),
                task=row.get("task", ""),
                context=row.get("context", ""),
                context_type=row.get("context_type", None),
                options=row.get("options", None),
                program=row.get("program", None),
            )
            task_inputs.append(task_input)
        except Exception as e:
            logging.warning(f"Failed to convert row {idx} to TaskInput: {e}")

    logging.info(f"Converted {len(task_inputs)} rows into TaskInput objects.")
    return task_inputs


def inputs_to_contexts(task_inputs: List[TaskInput]) -> List[TaskContext]:
    """
    Converts a list of TaskInput objects into a list of TaskContext objects.
    """
    return [TaskContext(input_data=input_data) for input_data in task_inputs]



def load_parquet(parquet_file_path):
    df = pd.read_parquet(parquet_file_path)
    return df

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

def load_finmath_dataset(file_path:str,top_n:int) -> DataFrame:

    data_finmath = FinMathDataset(file_path=file_path).get_dataset()
    if top_n is not None:
        data_finmath = data_finmath[:top_n]

    if len(data_finmath) == 0:
        exit(0)

    data = []

    for json_data in data_finmath:
        row = {
            "question": json_data.get("question", ""),
            "answer": json_data.get("ground_truth", None),
            "task": "FinancialMath",
            "context": "\n".join(json_data.get("tables", [])),
            "context_type": json_data.get("topic", ""),
            "options": None,
            "program": json_data.get("python_solution", None)
        }
        data.append(row)

    return pd.DataFrame(data)

def finmath_to_taskinput(dataset: DataFrame) -> List[TaskInput]:
    task_inputs = []

    for idx, row in dataset.iterrows():
        try:
            task_input = TaskInput(
                question=row.get("question", ""),
                answer=row.get("answer", None),
                task=row.get("task", ""),
                context=row.get("context", ""),
                context_type=row.get("context_type", None),
                options=row.get("options", None),
                program=row.get("program", None),
            )
            task_inputs.append(task_input)
        except Exception as e:
            logging.warning(f"Failed to convert row {idx} to TaskInput: {e}")

    logging.info(f"Converted {len(task_inputs)} rows into TaskInput objects.")
    return task_inputs

