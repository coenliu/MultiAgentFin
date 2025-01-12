# llm_interface.py

import logging
import json
from typing import List, Dict, Any
from openai import OpenAI

class OpenAIClient:
    """
    A client to interact with a vLLM server using an OpenAI-like API interface.
    """
    def __init__(self, api_key: str, base_url: str):
        try:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
            logging.info(f"OpenAIClient initialized with base_url: {base_url}")
        except Exception as e:
            logging.error(f"Failed to initialize OpenAIClient: {e}")
            raise

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: int = 42,
        extra_body: Dict[str, Any] = None,
    ) -> str:

        try:
            outputs = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                seed=seed,
                extra_body=extra_body,
            )
            raw_text = outputs.choices[0].message.content
            return self._process_output(raw_text)
        except Exception as e:
            raise RuntimeError(f"Error: Unable to post response to LLM server.")

    def _process_output(self, text: str) -> str:
        trimmed = text.strip()
        try:
            obj = json.loads(trimmed)
            return json.dumps(obj, indent=2)
        except json.JSONDecodeError:
            return trimmed