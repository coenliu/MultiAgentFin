import re
import json
from typing import Dict, Any


def extract_variables(input_text: str) -> str:
    """
    Extracts variables and their descriptions using regex from the input text.
    """
    pattern = r'"variables":\s*\{[^{}]*\}'
    matches = re.findall(pattern, input_text, re.IGNORECASE)

    if matches:
        return matches[-1]
    else:
        return "No 'variables' block found."

def split_variables_from_formula(input_text: str):
    variable_pattern = r'\b[A-Za-z_][A-Za-z0-9_]*\b'

    matches = re.findall(variable_pattern, input_text)

    exclude_keywords = {"Extracted", "Formula"}
    variables = [match for match in matches if match not in exclude_keywords]

    unique_variables = ", ".join(sorted(set(variables)))

    return unique_variables


def format_query_results(query_result: Dict[str, Any]) -> str:
    extracted_data = []

    if 'documents' not in query_result or 'metadatas' not in query_result:
        raise ValueError("The query result must contain 'documents' and 'metadatas' keys.")

    documents_outer = query_result.get('documents', [])
    metadatas_outer = query_result.get('metadatas', [])

    for doc_list, meta_list in zip(documents_outer, metadatas_outer):
        for doc, meta in zip(doc_list, meta_list):
            extracted_data.append({
                'document': doc,
                'metadata': meta
            })

    formatted_string = json.dumps(extracted_data, indent=4)

    return formatted_string


def extract_approved(input_text: str) -> bool:
    """
    Extracts the boolean value of the "Approved" field from the input text using regular expressions.
    """
    pattern = r'"Approved"\s*:\s*(true|false)'

    match = re.search(pattern, input_text, re.IGNORECASE)

    if match:
        approved_str = match.group(1).lower()
        return approved_str == 'true'
    else:
        return False

def recursive_extract_formula(data):
    """
    Recursively search through a dict or list for keys named "formula"
    (case-insensitive) and return a list of found string values.
    """
    formulas = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key.lower() == "formula" and isinstance(value, str) and value.strip():
                formulas.append(value.strip())
            else:
                formulas.extend(recursive_extract_formula(value))
    elif isinstance(data, list):
        for item in data:
            formulas.extend(recursive_extract_formula(item))
    return formulas


def extract_formula(input_text: str) -> str:
    """
    Extracts the formula from the input text using multiple strategies:
    """
    pattern_single = r'"formula"\s*:\s*"([^"]+)"'
    # Pattern for list format formula
    pattern_list = r'"formula"\s*:\s*\[(.*?)\]'

    # Find matches
    match_single = re.findall(pattern_single, input_text, re.IGNORECASE)
    match_list = re.findall(pattern_list, input_text, re.IGNORECASE)

    if match_list:
        # Extract individual formulas from the list
        formulas = re.findall(r'"(.*?)"', match_list[-1])
        return "\n".join(formulas) if formulas else "No 'formula' block found."

    return match_single[-1] if match_single else "No 'formula' block found."