import os
import numpy as np
import pandas as pd
import re


def extract_numbers(input_string, normalize_large=True, large_threshold=1_000_000, decimals=2):
    """ Extracts all numbers from the input string. """
    try:
        normalized_input = str(input_string).replace(",", "").strip()
        numbers = re.findall(r"[-+]?\$?\d*\.?\d+", normalized_input)
        cleaned_numbers = []
        for num in numbers:
            value = float(num.replace("$", "")) if '.' in num else int(num.replace("$", ""))
            if normalize_large and abs(value) >= large_threshold:
                value = round(value / large_threshold, decimals)
            cleaned_numbers.append(value)
        return cleaned_numbers
    except Exception as e:
        print(f"Error extracting numbers: {e}")
        return []


def normalize_number(value, decimals=1):
    """ Normalizes a number by removing commas and rounding it. """
    try:
        return round(float(str(value).replace(",", "").strip()), decimals)
    except ValueError:
        return None


def calculate_token_length(text):
    """ Calculates the number of tokens in the provided text. """
    try:
        return len(str(text).split())
    except Exception as e:
        print(f"Error calculating token length: {e}")
        return 0


def process_csv(file_path, answer_column, generated_text_column, tolerance=0.01):
    """ Reads and processes a CSV file for number extraction and token length calculation, and groups results by token length. """
    try:
        df = pd.read_csv(file_path)
        if answer_column not in df.columns or generated_text_column not in df.columns:
            print(f"Error: Missing required columns in {file_path}. Skipping...")
            return None, None

        df = df.dropna(subset=[answer_column, generated_text_column])

        # Extract numbers
        df['extracted_numbers'] = df[generated_text_column].apply(extract_numbers)

        # Calculate token length
        df['token_length'] = df[generated_text_column].apply(calculate_token_length)

        # Define token length buckets
        bins = [0, 16, 32, 64, 128, 256, 512]
        labels = ['0-16', '17-32', '33-64', '65-128', '129-256', '257-512']
        df['token_bucket'] = pd.cut(df['token_length'], bins=bins, labels=labels, right=True)

        # Compare extracted numbers with answers
        def is_within_tolerance(row):
            normalized_answer = normalize_number(row[answer_column])
            if normalized_answer is None:
                return False
            lower_bound = normalize_number(normalized_answer * (1 - tolerance))
            upper_bound = normalize_number(normalized_answer * (1 + tolerance))
            return any(lower_bound <= abs(float(num)) <= upper_bound for num in row['extracted_numbers'])

        df['is_correct'] = df.apply(is_within_tolerance, axis=1)
        correct_rate = (df['is_correct'].sum() / len(df)) * 100 if len(df) > 0 else 0

        # Calculate accuracy rate for each token length group
        grouped_accuracy = (
            df.groupby('token_bucket')['is_correct']
            .mean()
            .fillna(0)
            .mul(100)
            .round(2)
        )

        # Print file processing details
        print(f"Processed file: {file_path}")
        print(f"Total Correct: {df['is_correct'].sum()}/{len(df)}")
        print(f"Correct Rate: {correct_rate:.2f}%\n")
        print("Accuracy Rate by Token Length Group:")
        print(grouped_accuracy)
        print("-" * 40)

        return df, correct_rate

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None


def process_directory(directory_path, answer_column, generated_text_column, tolerance=0.01):
    """ Processes all CSV files in the specified directory and aggregates results. """
    all_results = []
    correct_rates = []

    for file_name in os.listdir(directory_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(directory_path, file_name)
            print(f"Processing file: {file_name}")
            try:
                df, correct_rate = process_csv(file_path, answer_column, generated_text_column, tolerance)
                if df is not None:
                    all_results.append(df)
                    correct_rates.append(correct_rate)
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    if all_results:
        combined_df = pd.concat(all_results, ignore_index=True)
        overall_correct_rate = np.mean(correct_rates) if correct_rates else 0
        correct_rate_variance = np.var(correct_rates) if correct_rates else 0

        print(f"\nOverall Correct Rate: {overall_correct_rate:.2f}%")
        print(f"Variance of Correct Rates: {correct_rate_variance:.4f}")
        return combined_df, overall_correct_rate, correct_rate_variance
    else:
        print("No valid data to process.")
        return pd.DataFrame(), 0, 0


# Example Usage
if __name__ == "__main__":
    directory_path = '../results/final_res/reason'  # Path to the directory with CSV files
    answer_column = 'answer'
    generated_text_column = 'model_output' #model_output generated_text
    tolerance = 0.02  # Adjust tolerance as needed

    # Process the directory and aggregate results
    combined_results, overall_correct_rate, correct_rate_variance = process_directory(
        directory_path, answer_column, generated_text_column, tolerance
    )

