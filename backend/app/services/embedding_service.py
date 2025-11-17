"""
Embedding service for generating vector embeddings from text.
Supports OpenAI embeddings with potential for other providers.
"""
from typing import List, Optional
import openai
from app.config import get_settings
import numpy as np

settings = get_settings()


class EmbeddingService:
    """
    Service for generating text embeddings using OpenAI or compatible APIs.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize embedding service.

        Args:
            api_key: OpenAI API key (uses settings default if not provided)
            model: Embedding model name (uses settings default if not provided)
        """
        self.api_key = api_key or settings.openai_api_key
        self.model = model or settings.embedding_model
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text string.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        # Clean and truncate text if needed
        text = text.strip()
        if not text:
            # Return zero vector for empty text
            return [0.0] * settings.embedding_dimension

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )

        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        Args:
            texts: List of text strings to embed

        Returns:
            List of embedding vectors (one per input text)
        """
        if not texts:
            return []

        # Clean texts
        cleaned_texts = [t.strip() if t.strip() else " " for t in texts]

        response = await self.client.embeddings.create(
            model=self.model,
            input=cleaned_texts,
        )

        # Sort by index to ensure order matches input
        embeddings_with_index = [(item.index, item.embedding) for item in response.data]
        embeddings_with_index.sort(key=lambda x: x[0])

        return [emb for _, emb in embeddings_with_index]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (-1 to 1, higher is more similar)
        """
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)

        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))


# Global embedding service instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """
    Get or create the global embedding service instance.

    Returns:
        Singleton embedding service
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
