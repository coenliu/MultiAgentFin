#!/usr/bin/env python3
"""
Data Augmentation Script for Formula Agent

This script reads sampled data from a JSON file, processes each question using OpenAI's GPT-4 API,
and saves the results (id, question, response) into a new JSON file.

Author: Your Name
Date: YYYY-MM-DD
"""

import json
import os
import argparse
import logging
import sys
import time
from dotenv import load_dotenv
from typing import List, Dict, Any
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='data_augment.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Set OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.error("OpenAI API key not found. Please set OPENAI_API_KEY in the .env file.")
    sys.exit("OpenAI API key not found. Please set OPENAI_API_KEY in the .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)


def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Reads a JSON file and returns its content.
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logging.info(f"Successfully read {len(data)} entries from '{file_path}'.")
        return data
    except FileNotFoundError:
        logging.error(f"File '{file_path}' not found.")
        sys.exit(f"File '{file_path}' not found.")
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from '{file_path}': {e}")
        sys.exit(f"Error decoding JSON from '{file_path}': {e}")


def process_question_with_openai(question: str, retries: int = 3, backoff_factor: float = 2.0) -> str:
    """
    Sends a question to the OpenAI model and retrieves the response.
    """
    #for instruct fine-tuning
    # messages = [
    #     {"role": "user", "content": f""" Task:Given a paragraph, generate five distinct expressions while preserving the original meaning. \n
    #     Instructions:
    #     • The paragraph is a scientific multiple-choice question (without options).
    #     • Keep the meaning unchanged; do not add extra or unrelated information.
    #     • Adjust sentence structure if necessary, but the meaning must remain the same.
    #     • Provide five variations, each separated by ”<sep >”. \n
    #      Question: {question}"""}
    # ]

    #for step fine-tuning,
    prompt = f"""
    You are an expert in financial analysis. Given the following question, provide the formula that can solve it, and explain each component of the formula in detail. \n
    Question: {question} \n
    Output Format: \n
    Formula: \n
    [LaTeX formatted formula] \n
    Components Explained: \n
    1. Component Name:
       - Definition: 
       - Symbol: 
    2. Component Name:
       - Definition: 
       - Symbol: 
    ...\n
    Step-by-Step Calculation:\n
    1. Step 1:
       - Description
    2. Step 2:
       - Description
    ...\n
    Ensure that the formula is correctly formatted using LaTeX syntax.
    """

    for attempt in range(1, retries + 1):
        try:
            response = client.chat.completions.create(
                model="o1-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            wait_time = backoff_factor ** attempt
            logging.error(f"Error during OpenAI API call: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    logging.error(f"Failed to get response for question after {retries} attempts.")
    return "Error: Unable to process question."


def augment_data_from_file(input_file: str, output_file: str, top_n: int = None):
    """
    Reads questions from a JSON file, processes each question with OpenAI, and saves the results incrementally.

    Parameters:
    - input_file: Path to the input JSON file.
    - output_file: Path to the output JSON file.
    - top_n: Number of top entries to process (optional).
    """
    data = read_json_file(input_file)

    if top_n is not None:
        data = data[:top_n]
        logging.info(f"Processing only the top {top_n} entries from the input file.")

    # Open the output file in write mode to create an empty list at the start
    with open(output_file, 'w') as f:
        json.dump([], f, indent=4)

    # Incrementally process questions and save results
    for idx, entry in enumerate(data):
        id_ = entry.get("id")
        question = entry.get("question")

        if not question:
            logging.warning(f"Skipping entry with ID {id_} due to missing question.")
            continue

        print(f"Processing question {idx + 1}/{len(data)}: ID {id_}")
        response = process_question_with_openai(question)
        result = {"id": id_, "question": question, "response": response}

        # Append result to the output file
        with open(output_file, 'r+') as f:
            existing_data = json.load(f)
            existing_data.append(result)
            f.seek(0)
            json.dump(existing_data, f, indent=4)
        logging.info(f"Saved result for ID {id_}")


def main():
    parser = argparse.ArgumentParser(description="Data Augmentation Script for Formula Agent")
    parser.add_argument('--input_file', type=str, required=True, help='Path to the input JSON file')
    parser.add_argument('--output_file', type=str, required=True, help='Path to the output JSON file')
    parser.add_argument('--top_n', type=int, default=None, help='Number of top entries to process (optional)')
    args = parser.parse_args()

    augment_data_from_file(args.input_file, args.output_file, args.top_n)


if __name__ == "__main__":
    main()


# Run Python command
#python3 data_augementation.py --input_file sampled_100_data.json --output_file augmented_results_top_10.json --top_n 10
#python3 data_augementation.py --input_file sampled_100_data.json --output_file augmented_question.json
#python3 data_augementation.py --input_file sampled_100_data.json --output_file augmented_results_step_o1mini_top_10.json --top_n 10
#python3 data_augementation.py --input_file sampled_100_data.json --output_file augmented_results_step.json