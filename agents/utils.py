import re
import json

def extract_variables(input_text: str) -> str:
    """
    Extracts variables and their descriptions using regex from the input text.
    """
    variables = []

    # Regex pattern to capture "variables" within a JSON-like structure
    json_pattern = r'```json\n.*?"variables"\s*:\s*{(.*?)}'
    json_match = re.search(json_pattern, input_text, re.DOTALL)

    if json_match:
        # Extract content within the "variables" key
        variables_content = json_match.group(1)
        # Extract keys and values from the variables content
        key_value_pattern = r'"(.*?)"\s*:\s*"(.*?)"'
        variables = [value.strip() for _, value in re.findall(key_value_pattern, variables_content)]
        print(f"Extracted variables from JSON-like content: {variables}")

    # Fallback to extracting variables from plain text
    if not variables:
        text_pattern = r"(?i)\bVariable\s*(\d+):?\s*(.+?)(?=\n|$)"
        matches = re.findall(text_pattern, input_text)
        variables = [desc.strip() for _, desc in matches]

    # Return a comma-separated string of unique variables
    return ", ".join(sorted(set(variables)))


def extract_formula(input_text: str) -> str:
    formula = None

    json_pattern = r'```json\n.*?"formula"\s*:\s*"(.*?)"'
    json_match = re.search(json_pattern, input_text, re.DOTALL)

    if json_match:
        formula_candidate = json_match.group(1).strip()
        if re.search(r"[+\-*/]", formula_candidate) and re.search(r"\d|[A-Za-z_]", formula_candidate):
            formula = formula_candidate

    if not formula:
        text_pattern = r"(?i)\bformula\b\s*[:\n]*\s*(.+?)(?=\n|$)"
        matches = re.findall(text_pattern, input_text)
        valid_formulas = [
            match.strip()
            for match in matches
            if re.search(r"[+\-*/]", match) and re.search(r"\d|[A-Za-z_]", match)
        ]
        if valid_formulas:
            formula = valid_formulas[-1]

    return formula if formula else "No valid formula found"


def split_variables_from_formula(input_text: str):
    variable_pattern = r'\b[A-Za-z_][A-Za-z0-9_]*\b'

    matches = re.findall(variable_pattern, input_text)

    exclude_keywords = {"Extracted", "Formula"}
    variables = [match for match in matches if match not in exclude_keywords]

    unique_variables = ", ".join(sorted(set(variables)))

    return unique_variables
