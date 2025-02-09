import json
from dataloader.parquet_dataset import ParquetDataset
from utils import setup_logger, load_config, load_parquet
import logging


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
        logging.warning(f"No samples found for task '{task_name}'.")
        exit(0)

    return dataset


def save_to_json_with_ids(data, output_file):
    """
    Saves the given data to a JSON file with unique IDs starting at 0.

    Parameters:
    - data: The data to save (list of dicts)
    - output_file: Path to the JSON file
    """
    try:
        # Add unique 0-based IDs to each record
        data_with_ids = [{"id": idx, **record} for idx, record in enumerate(data)]

        # Save to JSON file
        with open(output_file, 'w') as f:
            json.dump(data_with_ids, f, indent=4)

        logging.info(f"Data successfully saved to {output_file} with unique IDs starting at 0")
    except Exception as e:
        logging.error(f"Error saving data to {output_file}: {e}")
        raise


def select_100_dataset():
    data_path = "../bizBench/train-00000-of-00001-300a28d2e31daec3.parquet"
    task_name = "CodeFinQA"
    top_n = None
    dataset = load_and_prepare_dataset(data_path=data_path, task_name=task_name, top_n=top_n)

    # Sample 100 data points
    sampled_data = dataset.sample(100)

    # Convert to a serializable format if necessary
    sampled_data_serializable = sampled_data.to_dict(
        orient="records")  # Assuming `sampled_data` is a DataFrame-like object

    # Save to JSON with unique 0-based IDs
    output_file = "data_auge/sampled_100_data.json"
    save_to_json_with_ids(sampled_data_serializable, output_file)

    print(f"Sampled data has been saved to {output_file} with unique IDs starting at 0.")

