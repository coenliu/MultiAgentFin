from typing import Any, Dict, List, Tuple, Union
from rank_bm25 import BM25Okapi
import re
import logging

class BM25Model:
    def __init__(self, model_name: str, top_k: int = 4, **kwargs: Any) -> None:
        """
        Initialize the BM25-based model.

        Args:
            model_name (str): Name of the model.
            top_k (int): Number of top chunks to return for predictions.
            kwargs (Any): Additional arguments for BM25 configuration.
        """
        self._bm25 = None
        self._chunks = []
        self.top_k = top_k
        self.max_chunk_size = kwargs.get("max_chunk_size", 500)

    def get_top_chunks(self, query: str, passage: str, top_k: int = None) -> List[Dict[str, Union[str, float]]]:
        """
        Retrieve the most relevant chunks for the given query and passage.

        Args:
            query (str): The query text.
            passage (str): The mixed text and table passage.
            top_k (int, optional): Number of top chunks to return. Defaults to self.top_k.

        Returns:
            List[Dict[str, Union[str, float]]]: The top `top_k` most similar chunks with their similarity scores.
        """
        if not isinstance(query, str):
            raise ValueError(f"Query should be a string, but got {type(query).__name__}. Content: {query}")
        if not isinstance(passage, str):
            raise ValueError(f"Passage should be a string, but got {type(passage).__name__}. Content: {passage}")

        self._chunks = self.chunk_mixed_content(passage)
        self._setup_bm25_index(self._chunks)

        # Use the top_k parameter if provided; otherwise, use the class-level setting.
        top_k = top_k or self.top_k

        top_chunks = self._search_bm25(query, top_k)

        return self._format_top_chunks(top_chunks)

    def _setup_bm25_index(self, chunks: List[str]) -> None:
        """
        Set up the BM25 model with the given chunks.
        """
        tokenized_chunks = [self._tokenize(chunk) for chunk in chunks]
        self._bm25 = BM25Okapi(tokenized_chunks)

    def _search_bm25(self, query: str, top_k: int) -> List[Tuple[str, float]]:
        """
        Search the BM25 index with a given query and return the top results.
        """
        tokenized_query = self._tokenize(query)
        scores = self._bm25.get_scores(tokenized_query)

        # Combine scores with chunks and sort by relevance
        ranked_chunks = sorted(
            zip(self._chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )
        return ranked_chunks[:top_k]  # Return the specified number of top chunks

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize the input text for BM25.
        """
        return text.lower().split()

    def _format_top_chunks(self, top_chunks: List[Tuple[str, float]]) -> List[Dict[str, Union[str, float]]]:
        """
        Format the top chunks and their similarity scores into a structured list.

        Args:
            top_chunks (List[Tuple[str, float]]): The top chunks with their similarity scores.

        Returns:
            List[Dict[str, Union[str, float]]]: A list of dictionaries with chunk content and score.
        """
        formatted_chunks = [
            {"chunk": chunk, "score": score}
            for chunk, score in top_chunks
        ]
        return formatted_chunks


    def chunk_mixed_content(self, passages: str, max_chunk_size: int = 500) -> List[str]:
        """
        Chunk a mixed content of paragraphs and tables into manageable pieces.
        Each paragraph is treated as a single chunk, and each table is treated as a single chunk.

        Args:
            passages (str): The input passage containing mixed text and table data.
            max_chunk_size (int): The maximum size of each chunk.

        Returns:
            List[str]: A list of chunks.
        """
        lines = passages.splitlines()
        chunks = []
        current_paragraph = []
        current_table = []

        def flush_paragraph():
            """Combine and add the current paragraph lines as a single chunk."""
            if current_paragraph:
                paragraph_text = " ".join(current_paragraph).strip()
                if paragraph_text:
                    chunks.append(paragraph_text)
                current_paragraph.clear()

        def flush_table():
            """Combine and add the current table lines as a single chunk."""
            if current_table:
                table_text = "\n".join(current_table).strip()
                if table_text:
                    chunks.append(table_text)
                current_table.clear()

        for line in lines:
            stripped_line = line.strip()

            if stripped_line.startswith("|") and re.match(r"\|\s*[-:]+", stripped_line):
                # Recognize the start of a table header (e.g., "| --- | --- |")
                flush_paragraph()
                current_table.append(stripped_line)
            elif stripped_line.startswith("|"):
                # Recognize a table row
                current_table.append(stripped_line)
            else:
                # Recognize a paragraph line
                if current_table:
                    flush_table()
                if stripped_line:
                    current_paragraph.append(stripped_line)
                else:
                    flush_paragraph()

        # Flush any remaining paragraph or table at the end
        flush_paragraph()
        flush_table()

        final_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                sentences = re.split(r'(?<=[.?!])\s+', chunk)  # Split by sentence boundary
                temp_chunk = []
                current_size = 0
                for sentence in sentences:
                    if current_size + len(sentence) > max_chunk_size:
                        final_chunks.append(" ".join(temp_chunk))
                        temp_chunk = []
                        current_size = 0
                    temp_chunk.append(sentence)
                    current_size += len(sentence) + 1
                if temp_chunk:
                    final_chunks.append(" ".join(temp_chunk))
            else:
                final_chunks.append(chunk)

        return final_chunks