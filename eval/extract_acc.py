import os
import numpy as np
import pandas as pd
import re

def extract_numbers(input_string):
    """
    Extracts all numbers from the input string, handling formats like:
    "Conclusion: 123", "$3.76", or "Conclusion: [[456]]".
    """
    try:
        # Normalize input by removing commas and trimming whitespace
        normalized_input = str(input_string).replace(",", "").strip()

        # Match numbers, including decimals and optional currency symbols
        numbers = re.findall(r"[-+]?\$?\d*\.?\d+", normalized_input)

        # Convert extracted numbers to float or int
        cleaned_numbers = [
            float(num.replace("$", "")) if '.' in num else int(num.replace("$", ""))
            for num in numbers
        ]
        return cleaned_numbers
    except Exception as e:
        print(f"Error extracting numbers: {e}")
        return []

def normalize_number(value):
    """
    Normalizes a numeric value:
    - Removes commas and trims spaces.
    - Converts numbers (even '85.0') to float.
    """
    try:
        return float(str(value).replace(",", "").strip())
    except ValueError:
        return None

def process_csv(file_path, answer_column, generated_text_column):
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

        # Compare extracted numbers with answers
        df['is_correct'] = df.apply(lambda row: normalize_number(row[answer_column]) in
                                    [abs(float(num))  for num in row['extracted_numbers']], axis=1)

        # Calculate the correct rate
        correct_rate = (df['is_correct'].sum() / len(df)) * 100 if len(df) > 0 else 0

        print(f"Processed file: {file_path}")
        # print("Answer | Extracted Numbers | Correct")
        # print("-" * 40)
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

def process_directory(directory_path, answer_column, generated_text_column):
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
                df, correct_rate = process_csv(file_path, answer_column, generated_text_column)
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
    directory_path = '../results/final_res/extract'  # Path to the directory with CSV files
    answer_column = 'answer'
    generated_text_column = 'model_output' #model_output,intermediate_data

    # Process the directory and aggregate results
    combined_results, overall_correct_rate, correct_rate_variance = process_directory(
        directory_path, answer_column, generated_text_column
    )

    # Save combined results to a new CSV file
    # if not combined_results.empty:
    #     combined_results.to_csv("aggregated_results.csv", index=False)
    #     print("Aggregated results saved to aggregated_results.csv")