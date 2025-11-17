"""
Planner Agent: Analyzes user queries and creates retrieval plans.
"""
from typing import Optional
import json
from datetime import datetime, timedelta, date
import re

from app.agents.base import BaseAgent, PlannerOutput
from app.services.llm_client import get_llm_client


class PlannerAgent(BaseAgent):
    """
    Planner Agent analyzes the user's question and extracts:
    - Temporal scope (specific date, date range, or None)
    - Key topics and entities
    - Subtasks for retrieval
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    async def execute(self, question: str, current_date: date = None) -> PlannerOutput:
        """
        Analyze question and create a retrieval plan.

        Args:
            question: User's question
            current_date: Current date for temporal reference (defaults to today)

        Returns:
            PlannerOutput with temporal scope, topics, entities, and subtasks
        """
        if current_date is None:
            current_date = date.today()

        # Use LLM to extract temporal scope and key concepts
        prompt = self._create_planning_prompt(question, current_date)

        messages = [
            {"role": "system", "content": "You are an expert at analyzing questions and extracting temporal information, topics, and entities. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )

            # Parse LLM response - extract JSON from response (handles markdown code blocks)
            plan_data = self._extract_json_from_response(response)

            # Extract temporal scope
            temporal_scope = self._parse_temporal_scope(
                plan_data.get("temporal_scope", {}),
                current_date
            )

            # Refine temporal scope if too broad
            if temporal_scope and temporal_scope.get("type") == "range":
                temporal_scope = self._refine_temporal_scope(
                    temporal_scope, question, current_date
                )

            planner_output = PlannerOutput(
                temporal_scope=temporal_scope,
                topics=plan_data.get("topics", []),
                entities=plan_data.get("entities", []),
                subtasks=plan_data.get("subtasks", "")
            )

            return planner_output

        except Exception as e:
            print(f"Planner agent failed: {e}")
            # Return default plan
            return PlannerOutput(
                temporal_scope=None,
                topics=[],
                entities=[],
                subtasks="Retrieve relevant information and answer the question."
            )

    def _create_planning_prompt(self, question: str, current_date: date) -> str:
        """
        Create the planning prompt for the LLM.
        """
        return f"""Analyze the following question and extract structured information.
Today's date is {current_date.strftime('%Y-%m-%d')} ({current_date.strftime('%A, %B %d, %Y')}).

Question: "{question}"

Extract the following:
1. Temporal scope: When is the user asking about?
   - If asking about a specific day (e.g., "yesterday", "last Tuesday", "June 15th"), return the specific date
   - If asking about a period (e.g., "last week", "this month"), return a date range
   - If no temporal reference, return null

2. Topics: Main themes or subjects (e.g., "machine learning", "project planning")

3. Entities: Specific names of people, organizations, projects, etc.

4. Subtasks: Brief description of what retrieval should focus on

Respond in JSON format:
{{
  "temporal_scope": {{
    "type": "date|range|none",
    "date": "YYYY-MM-DD",  // if type is "date"
    "start_date": "YYYY-MM-DD",  // if type is "range"
    "end_date": "YYYY-MM-DD",  // if type is "range"
    "description": "natural language description"
  }},
  "topics": ["topic1", "topic2"],
  "entities": ["Entity 1", "Entity 2"],
  "subtasks": "Focus on X and find information about Y"
}}"""

    def _parse_temporal_scope(
        self,
        temporal_data: dict,
        current_date: date
    ) -> Optional[dict]:
        """
        Parse and normalize temporal scope data.
        """
        scope_type = temporal_data.get("type", "none")

        if scope_type == "none":
            return None

        if scope_type == "date":
            date_str = temporal_data.get("date")
            if date_str:
                try:
                    parsed_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    return {
                        "type": "date",
                        "date": parsed_date,
                        "description": temporal_data.get("description", "")
                    }
                except ValueError:
                    return None

        if scope_type == "range":
            start_str = temporal_data.get("start_date")
            end_str = temporal_data.get("end_date")
            if start_str and end_str:
                try:
                    start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
                    end_date = datetime.strptime(end_str, "%Y-%m-%d").date()
                    return {
                        "type": "range",
                        "start_date": start_date,
                        "end_date": end_date,
                        "description": temporal_data.get("description", "")
                    }
                except ValueError:
                    return None

        return None

    def _refine_temporal_scope(
        self,
        temporal_scope: dict,
        question: str,
        current_date: date
    ) -> dict:
        """
        Refine temporal scope if it's too broad.
        If the range is more than 30 days, narrow it based on question keywords.
        """
        if temporal_scope.get("type") != "range":
            return temporal_scope

        start_date = temporal_scope["start_date"]
        end_date = temporal_scope["end_date"]
        days_diff = (end_date - start_date).days

        # If range is reasonable, keep it
        if days_diff <= 30:
            return temporal_scope

        # If too broad, narrow to most recent week of the range
        # (This is a simple heuristic; could be more sophisticated)
        narrowed_start = end_date - timedelta(days=7)

        return {
            "type": "range",
            "start_date": narrowed_start,
            "end_date": end_date,
            "description": f"Narrowed from broader range to most recent week"
        }

    def _extract_json_from_response(self, response: str) -> dict:
        """
        Extract JSON from LLM response, handling markdown code blocks and extra text.

        Args:
            response: Raw LLM response that may contain JSON wrapped in markdown or extra text

        Returns:
            Parsed JSON dict

        Raises:
            json.JSONDecodeError: If no valid JSON found
        """
        # Try parsing directly first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks (```json ... ```)
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try finding JSON object anywhere in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        # If all else fails, raise error
        raise json.JSONDecodeError(f"Could not extract valid JSON from response: {response[:200]}", response, 0)
