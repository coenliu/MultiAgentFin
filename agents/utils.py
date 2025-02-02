import re
import json
from typing import Dict, Any


def extract_variables(input_text: str) -> str:
    """
    Extracts variables and their descriptions using regex from the input text.
    """
    variables = []
    json_block_pattern = r'```json\s*(\{.*?\})\s*```'
    json_blocks = re.findall(json_block_pattern, input_text, re.DOTALL)

    json_content = None
    if json_blocks:
        # Use the last JSON block found.
        json_content = json_blocks[-1]
    else:
        # Fallback: try to extract any JSON-like object that contains "variables"
        json_object_pattern = r'(\{.*"variables"\s*:\s*\{.*?\}.*\})'
        json_objects = re.findall(json_object_pattern, input_text, re.DOTALL)
        if json_objects:
            json_content = json_objects[-1]

    # If we have some JSON content, try to parse it.
    if json_content:
        try:
            data = json.loads(json_content)
            if "variables" in data and isinstance(data["variables"], dict):
                # Build variables list from the JSON object.
                for key, value in data["variables"].items():
                    # Convert value to string in case it is numeric.
                    variables.append(f"{key.strip()}: {str(value).strip()}")
                print(f"Extracted variables from JSON content: {variables}")
        except json.JSONDecodeError as e:
            print("Error parsing JSON content:", e)

    # Fallback to text-based extraction if no variables were found in JSON.
    if not variables:
        text_pattern = r"(?i)\bVariable\s*(\d+):?\s*(.+?)(?=\n|$)"
        matches = re.findall(text_pattern, input_text)
        if matches:
            number, desc = matches[-1]
            variables = [f"Variable {number.strip()}: {desc.strip()}"]
        else:
            return "not found"
    return ", ".join(sorted(set(variables)))





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
    formula = None

    # -- Step 1: JSON extraction --
    # Look for a JSON block fenced with triple backticks.
    json_block_pattern = r'```json\s*(\{.*?\})\s*```'
    json_blocks = re.findall(json_block_pattern, input_text, re.DOTALL)

    json_content = None
    if json_blocks:
        json_content = json_blocks[-1]
    else:
        # Fallback: try to extract any JSON-like object that contains "formula"
        json_object_pattern = r'(\{.*"formula".*\})'
        json_objects = re.findall(json_object_pattern, input_text, re.DOTALL)
        if json_objects:
            json_content = json_objects[-1]

    if json_content:
        try:
            data = json.loads(json_content)
            # First try a top-level "formula" key.
            if "formula" in data and isinstance(data["formula"], str) and data["formula"].strip():
                formula = data["formula"].strip()
            else:
                # If not found, recursively search for any nested "formula" keys.
                formulas = recursive_extract_formula(data)
                if formulas:
                    # Take the last found formula.
                    formula = formulas[-1]
            # Uncomment the next line to debug JSON extraction.
            # print(f"Extracted formula from JSON: {formula}")
        except json.JSONDecodeError as e:
            print("Error parsing JSON content for formula:", e)

    # -- Step 2: Section extraction --
    if not formula:
        # Look for a "**Formula:**" section and capture its content until the next section marker (e.g., ** or end of text).
        formula_section_pattern = r"\*\*Formula:\*\*\s*(.*?)\s*(?=\*\*|$)"
        match = re.search(formula_section_pattern, input_text, re.DOTALL)
        if match:
            formula_candidate = match.group(1).strip()
            if formula_candidate:
                formula = formula_candidate


    # -- Step 3: Fallback text extraction --
    if not formula:
        # Look for a line that starts with "Formula" followed by ':' or '=' and capture the rest of the line.
        text_pattern = r"(?i)\bFormula\s*[:=]\s*(.+?)(?=\n|$)"
        matches = re.findall(text_pattern, input_text)
        if matches:
            formula = matches[-1].strip()
        else:
            return "not found"

    return formula if formula else "not found"