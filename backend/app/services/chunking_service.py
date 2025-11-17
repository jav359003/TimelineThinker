"""
Text chunking service for breaking documents into semantic chunks.
"""
from typing import List, Tuple
from app.config import get_settings
import re

settings = get_settings()


class ChunkingService:
    """
    Service for chunking text into overlapping segments for better retrieval.

    Uses a sliding window approach with configurable size and overlap.
    Attempts to break on sentence boundaries when possible.
    """

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Initialize chunking service.

        Args:
            chunk_size: Target number of tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def _simple_tokenize(self, text: str) -> List[str]:
        """
        Simple word-based tokenization for chunking.
        For production, consider using tiktoken for accurate token counts.

        Args:
            text: Input text

        Returns:
            List of word tokens
        """
        return text.split()

    def _find_sentence_boundary(self, tokens: List[str], target_idx: int) -> int:
        """
        Find the nearest sentence boundary to target index.

        Args:
            tokens: List of tokens
            target_idx: Target index to find boundary near

        Returns:
            Index of sentence boundary
        """
        # Look backward from target for sentence-ending punctuation
        search_start = max(0, target_idx - 50)
        search_end = min(len(tokens), target_idx + 50)

        for i in range(target_idx, search_start, -1):
            if i < len(tokens) and re.match(r'.*[.!?]$', tokens[i]):
                return i + 1

        # If no boundary found backward, look forward
        for i in range(target_idx, search_end):
            if i < len(tokens) and re.match(r'.*[.!?]$', tokens[i]):
                return i + 1

        # Fall back to target index
        return target_idx

    def chunk_text(self, text: str) -> List[Tuple[str, int]]:
        """
        Chunk text into overlapping segments.

        Args:
            text: Input text to chunk

        Returns:
            List of tuples (chunk_text, chunk_index)
        """
        if not text.strip():
            return []

        tokens = self._simple_tokenize(text)

        if len(tokens) <= self.chunk_size:
            # Text is small enough to be a single chunk
            return [(text, 0)]

        chunks = []
        chunk_idx = 0
        start_idx = 0

        while start_idx < len(tokens):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(tokens))

            # Try to end on sentence boundary if not at the end
            if end_idx < len(tokens):
                end_idx = self._find_sentence_boundary(tokens, end_idx)

            # Extract chunk tokens and reconstruct text
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = ' '.join(chunk_tokens)

            chunks.append((chunk_text, chunk_idx))

            # Move start index forward, accounting for overlap
            start_idx = end_idx - self.chunk_overlap
            if start_idx >= len(tokens) - self.chunk_overlap:
                break

            chunk_idx += 1

        return chunks

    def chunk_text_by_sentences(self, text: str, max_chunk_size: int = None) -> List[Tuple[str, int]]:
        """
        Alternative chunking strategy: group sentences up to max size.

        Args:
            text: Input text to chunk
            max_chunk_size: Maximum tokens per chunk

        Returns:
            List of tuples (chunk_text, chunk_index)
        """
        max_size = max_chunk_size or self.chunk_size

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_idx = 0

        for sentence in sentences:
            sentence_length = len(self._simple_tokenize(sentence))

            if current_length + sentence_length > max_size and current_chunk:
                # Finalize current chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append((chunk_text, chunk_idx))

                # Start new chunk with overlap (last sentence)
                current_chunk = [current_chunk[-1]] if current_chunk else []
                current_length = len(self._simple_tokenize(current_chunk[0])) if current_chunk else 0
                chunk_idx += 1

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append((chunk_text, chunk_idx))

        return chunks


def get_chunking_service() -> ChunkingService:
    """
    Get a chunking service instance.

    Returns:
        ChunkingService instance
    """
    return ChunkingService()
