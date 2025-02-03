import chromadb
from chromadb.config import Settings

import json
import uuid
from typing import List, Dict, Optional
import os
class FormulaRetriever:
    def __init__(self, collection_name: str):
        """
        Initializes the FormulaRetriever with a specified collection and loads JSON data.
        """
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_url = os.path.join(script_dir, "formula.json")

        self.chroma_client = chromadb.Client(Settings(
            persist_directory=os.path.join(script_dir, "chroma_db"),
            anonymized_telemetry=False
        ))
        self.collection = self._initialize_collection(collection_name)
        self.data = self._load_json_data(data_url)
        self.add_chunks_to_collection()

    def _load_json_data(self, data_url: str) -> List[Dict[str, str]]:
        """
        Loads JSON data from a specified file path.
        """
        try:
            with open(data_url, "r") as f:
                data = json.load(f)
            print(f"Loaded JSON data from '{data_url}'.")
            return data
        except FileNotFoundError:
            print(f"Error: The file '{data_url}' was not found.")
            return []
        except json.JSONDecodeError:
            print(f"Error: The file '{data_url}' contains invalid JSON.")
            return []

    def _initialize_collection(self, collection_name: str):
        try:
            collection = self.chroma_client.create_collection(name=collection_name)
            print(f"Accessed existing collection '{collection_name}'.")
        except chromadb.errors.InvalidCollectionException:
            collection = self.chroma_client.create_collection(name=collection_name)
            print(f"Created new collection '{collection_name}'.")
        return collection

    @staticmethod
    def split_json_into_chunks(data: List[Dict[str, str]]) -> List[Dict[str, str]]:
        chunks = []
        for entry in data:
            if 'formula_name' in entry and 'formula' in entry:
                chunk = {key: entry[key] for key in entry if key in ['formula_name', 'formula', 'meaning']}
                chunks.append(chunk)
        print(f"Split data into {len(chunks)} chunks.")
        return chunks

    def add_chunks_to_collection(self) -> None:
        """
        Processes the loaded JSON data and adds chunks to the Chroma collection.
        """
        if not self.data:
            print("No data to add to the collection.")
            return

        chunks = self.split_json_into_chunks(self.data)
        texts = [chunk["formula"] for chunk in chunks]  # Texts to embed (the formula content)
        metadatas = [
            {
                "formula_name": chunk["formula_name"],
                "meaning": chunk.get("meaning", "")
            } for chunk in chunks
        ]
        ids = [str(uuid.uuid4()) for _ in chunks]  # Generate a unique UUID for each chunk

        try:
            self.collection.add(documents=texts, metadatas=metadatas, ids=ids)
            print(f"Added {len(chunks)} chunks to the collection '{self.collection.name}'.")
        except Exception as e:
            print(f"Error adding chunks to collection: {e}")

    def query_collection(self, query: str, n_results: int = 2) -> Optional[Dict]:
        """
        Queries the Chroma collection for similar documents.
        """
        try:
            results = self.collection.query(query_texts=[query], n_results=n_results)
            return results
        except Exception as e:
            print(f"Error querying collection: {e}")
            return None