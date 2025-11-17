"""
Entity and topic extraction service using LLM.
"""
from typing import List, Dict, Tuple
import json
from app.services.llm_client import get_llm_client


class EntityExtractionService:
    """
    Service for extracting entities and topics from text using LLM.

    Uses structured prompting to extract:
    - Named entities (people, organizations, locations)
    - Topics/themes
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    async def extract_entities_and_topics(self, text: str) -> Tuple[List[Dict], List[str]]:
        """
        Extract entities and topics from text.

        Args:
            text: Input text to analyze

        Returns:
            Tuple of (entities, topics) where:
            - entities is list of dicts: [{"name": str, "type": str, "confidence": int}]
            - topics is list of topic strings
        """
        if not text.strip():
            return [], []

        prompt = f"""Analyze the following text and extract:
1. Named entities (people, organizations, locations, etc.)
2. Main topics or themes

Text:
\"\"\"
{text[:2000]}  # Limit to first 2000 chars for efficiency
\"\"\"

Respond in JSON format:
{{
  "entities": [
    {{"name": "entity name", "type": "PERSON|ORG|GPE|OTHER", "confidence": 85}}
  ],
  "topics": ["topic1", "topic2"]
}}

Only include entities and topics that are clearly relevant. Limit to top 5 of each."""

        messages = [
            {"role": "system", "content": "You are an expert at extracting structured information from text. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )

            # Parse JSON response
            result = json.loads(response)
            entities = result.get("entities", [])
            topics = result.get("topics", [])

            return entities, topics

        except Exception as e:
            # If extraction fails, return empty lists
            print(f"Entity extraction failed: {e}")
            return [], []

    async def extract_entities_simple(self, text: str) -> List[Dict]:
        """
        Simplified entity extraction (entities only).

        Args:
            text: Input text

        Returns:
            List of entity dicts
        """
        entities, _ = await self.extract_entities_and_topics(text)
        return entities

    async def extract_topics_simple(self, text: str) -> List[str]:
        """
        Simplified topic extraction (topics only).

        Args:
            text: Input text

        Returns:
            List of topic strings
        """
        _, topics = await self.extract_entities_and_topics(text)
        return topics


def get_entity_extraction_service() -> EntityExtractionService:
    """
    Get entity extraction service instance.

    Returns:
        EntityExtractionService instance
    """
    return EntityExtractionService()
