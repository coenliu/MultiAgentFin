# import json
# import re
#
# def process_augmented_questions(input_file: str, output_file: str):
#     """
#     Processes the augmented_question.json file to split responses by <sep> and saves the results
#     to a new JSON file with the original id and question.
#
#     Parameters:
#         input_file (str): Path to the input JSON file.
#         output_file (str): Path to the output JSON file.
#     """
#     try:
#         # Read the input JSON file
#         with open(input_file, 'r') as infile:
#             data = json.load(infile)
#
#         processed_data = []
#
#         # Process each entry
#         for entry in data:
#             entry_id = entry.get("id")
#             question = entry.get("question")
#             response = entry.get("response")
#
#             if response:
#                 # Split the response by <sep>
#                 split_responses = [resp.strip() for resp in response.split('<sep>') if resp.strip()]
#
#                 # Create a new dictionary with required fields
#                 processed_entry = {
#                     "id": entry_id,
#                     "question": question,
#                     "responses": split_responses
#                 }
#
#                 processed_data.append(processed_entry)
#
#         # Save the processed data to the output file
#         with open(output_file, 'w') as outfile:
#             json.dump(processed_data, outfile, indent=4)
#
#         print(f"Processed data successfully saved to '{output_file}'.")
#
#     except Exception as e:
#         print(f"An error occurred: {e}")
#
# # File paths
# # input_file = "data_auge/augmented_question.json"
# # output_file = "processed_questions.json"
# #
# # # Process the data
# # process_augmented_questions(input_file, output_file)
#
# def process_flat_augmented_questions(input_file: str, output_file: str):
#     """
#     Processes the augmented_question.json file to create a flat list of question-response pairs,
#     each with the original id and question.
#
#     Parameters:
#         input_file (str): Path to the input JSON file.
#         output_file (str): Path to the output JSON file.
#     """
#     try:
#         # Read the input JSON file
#         with open(input_file, 'r') as infile:
#             data = json.load(infile)
#
#         processed_data = []
#
#         # Process each entry
#         for entry in data:
#             entry_id = entry.get("id")
#             question = entry.get("question")
#             responses = entry.get("responses", [])
#
#             for response in responses:
#                 processed_entry = {
#                     "id": entry_id,
#                     "question": response.strip()
#                 }
#                 processed_data.append(processed_entry)
#
#         # Save the processed data to the output file
#         with open(output_file, 'w') as outfile:
#             json.dump(processed_data, outfile, indent=4)
#
#         print(f"Processed data successfully saved to '{output_file}'.")
#
#     except Exception as e:
#         print(f"An error occurred: {e}")
#
# # File paths
# # input_file = "processed_questions.json"
# # output_file = "processed_flat_questions.json"
# #
# # # Process the data
# # process_flat_augmented_questions(input_file, output_file)
#
# def extract_formula(response):
#     """
#     Extract the formula from the response text.
#     The formula is expected to be between '**Formula:**' and the next section or end.
#     """
#     formula_match = re.search(r"\*\*Formula:\*\*\s*(.*?)\*\*", response, re.DOTALL)
#     if not formula_match:
#         # Alternative fallback if no '**' terminates the formula section
#         formula_match = re.search(r"\*\*Formula:\*\*\s*(.+)", response, re.DOTALL)
#     return formula_match.group(1).strip() if formula_match else None
#
#
# def process_augmented_results(augmented_results_file, processed_questions_file, output_file):
#     """
#     Process the augmented results to extract formulas and add them to processed questions.
#     """
#     try:
#         # Load input JSON files
#         with open(augmented_results_file, 'r') as results_file:
#             augmented_results = json.load(results_file)
#
#         with open(processed_questions_file, 'r') as questions_file:
#             processed_questions = json.load(questions_file)
#
#         # Create a dictionary to store formulas by ID
#         id_to_formula = {}
#         for entry in augmented_results:
#             formula = extract_formula(entry.get("response", ""))
#             if formula:
#                 id_to_formula[entry["id"]] = formula
#
#         # Add the formula to each question
#         enriched_questions = []
#         for question in processed_questions:
#             question_id = question["id"]
#             formula = id_to_formula.get(question_id, None)
#             enriched_entry = {
#                 # "id": question_id,
#                 "instruction": question["question"],
#                 "input": "",
#                 "output": formula
#             }
#             enriched_questions.append(enriched_entry)
#
#         # Save the enriched data to the output file
#         with open(output_file, 'w') as outfile:
#             json.dump(enriched_questions, outfile, indent=4)
#
#         print(f"Enriched data successfully saved to '{output_file}'.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#
#
# # File paths
# augmented_results_file = "data_auge/augmented_results_step.json"
# processed_questions_file = "data_auge/processed_flat_questions.json"
# output_file = "question_step_final.json"
#
# # Process the data
# process_augmented_results(augmented_results_file, processed_questions_file, output_file)

import json


def transform_json(file_path, output_path):
    """
    Reads a JSON file, replaces 'question' with 'instruction' and 'response' with 'output',
    and excludes the 'id' field. Saves the transformed data to a new JSON file.

    :param file_path: Path to the input JSON file.
    :param output_path: Path to save the transformed JSON file.
    """
    with open(file_path, 'r', encoding='utf-8') as infile:
        data = json.load(infile)

    # Transform the data
    transformed_data = []
    for item in data:
        transformed_item = {
            "instruction": item.get("question"),
            "input":"",
            "output": item.get("response")
        }
        transformed_data.append(transformed_item)

    # Save the transformed data
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(transformed_data, outfile, indent=4, ensure_ascii=False)


transform_json('final_data/augmented_results_step.json', 'results_step_final.json')