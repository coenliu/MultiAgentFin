# utils.py

import logging
import yaml
import os
import pandas as pd
from typing import Dict, Any

def setup_logger(log_level: str = "INFO", log_file: str = "logs/app.log") -> None:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def load_config(config_path: str = "configs/config.yaml") -> Dict[str, Any]:
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        logging.info(f"Loaded config from {config_path}")
        return data
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        return {}

def load_parquet(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_parquet(file_path)
        logging.info(f"Loaded data from {file_path}")
        return df
    except Exception as e:
        logging.error(f"Failed to load Parquet {file_path}: {e}")
        raise
