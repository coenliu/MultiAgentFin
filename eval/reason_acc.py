import os
import numpy as np
import pandas as pd
import re

def extract_numbers(input_string, normalize_large=True, large_threshold=1_000_000, decimals=2):
    """
    Extracts all numbers from the input string, handling formats like:
    "$3.76", "123", or "[[456]]".
    """
    try:
        # Normalize input by removing commas and trimming whitespace
        normalized_input = str(input_string).replace(",", "").strip()

        # Match numbers, including decimals and optional currency symbols
        numbers = re.findall(r"[-+]?\$?\d*\.?\d+", normalized_input)

        # Convert extracted numbers to float or int
        cleaned_numbers = []
        for num in numbers:
            # Convert to float or int
            value = float(num.replace("$", "")) if '.' in num else int(num.replace("$", ""))
            # Normalize if value exceeds the threshold
            if normalize_large and abs(value) >= large_threshold:
                value = round(value / large_threshold, decimals)
            cleaned_numbers.append(value)

        return cleaned_numbers
    except Exception as e:
        print(f"Error extracting numbers: {e}")
        return []


def normalize_number(value, decimals=1):

    try:
        return round(float(str(value).replace(",", "").strip()), decimals)
    except ValueError:
        return None

def process_csv(file_path, answer_column, generated_text_column, tolerance=0.01):
    """
    Reads a CSV file, validates required columns, and processes rows for number extraction.
    """
    try:
        # Read the file
        df = pd.read_csv(file_path)

        # Validate that required columns exist
        if answer_column not in df.columns or generated_text_column not in df.columns:
            print(f"Error: Missing required columns in {file_path}. Skipping...")
            return None, None

        # Drop rows where generated text or answer is missing
        df = df.dropna(subset=[answer_column, generated_text_column])

        # Apply extract_numbers function
        df['extracted_numbers'] = df[generated_text_column].apply(extract_numbers)

        # Compare extracted numbers with answers using tolerance
        def is_within_tolerance(row):
            normalized_answer = normalize_number(row[answer_column])
            if normalized_answer is None:
                return False
            lower_bound = normalize_number(normalized_answer * (1 - tolerance))
            upper_bound = normalize_number(normalized_answer * (1 + tolerance))
            # Check if any extracted number is within the range
            return any(lower_bound <= abs(float(num)) <= upper_bound for num in row['extracted_numbers'])

        df['is_correct'] = df.apply(is_within_tolerance, axis=1)

        # Calculate the correct rate
        correct_rate = (df['is_correct'].sum() / len(df)) * 100 if len(df) > 0 else 0

        print(f"Processed file: {file_path}")
        print("Answer | Extracted Numbers | Correct")
        print("-" * 40)
        # for index, row in df.iterrows():
        #     if not row['is_correct']:
        #         normalized_answer = normalize_number(row[answer_column])
        #         print(f"{normalized_answer} | {row['extracted_numbers']} | {row['is_correct']}")

        print(f"Total Correct: {df['is_correct'].sum()}/{len(df)}")
        print(f"Correct Rate: {correct_rate:.2f}%\n")

        return df, correct_rate

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None

def process_directory(directory_path, answer_column, generated_text_column, tolerance=0.01):
    """
    Processes all CSV files in the specified directory.
    """
    all_results = []
    correct_rates = []

    for file_name in os.listdir(directory_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(directory_path, file_name)
            print(f"Processing file: {file_name}")
            try:
                df, correct_rate = process_csv(file_path, answer_column, generated_text_column, tolerance)
                if df is not None:  # Add only valid DataFrames
                    all_results.append(df)
                    correct_rates.append(correct_rate)
            except Exception as e:
                print(f"Error processing file {file_name}: {e}")

    # Ensure all_results is not empty before concatenation
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
    directory_path = '../results/finmath'  # Path to the directory with CSV files
    answer_column = 'answer'
    generated_text_column = 'model_output'
    tolerance = 0.02  # Adjust tolerance as needed

    # Process the directory and aggregate results
    combined_results, overall_correct_rate, correct_rate_variance = process_directory(
        directory_path, answer_column, generated_text_column, tolerance
    )

    # Save combined results to a new CSV file
    # if not combined_results.empty:
    #     combined_results.to_csv("aggregated_results.csv", index=False)
    #     print("Aggregated results saved to aggregated_results.csv")