"""
Synthesizer Agent: Generates final answer from retrieved context.
"""
from typing import List
import json

from app.agents.base import (
    BaseAgent,
    PlannerOutput,
    TimelineChunk,
    DocumentChunk,
    AlignmentOutput,
    QueryResult
)
from app.services.llm_client import get_llm_client


class SynthesizerAgent(BaseAgent):
    """
    Synthesizer Agent generates the final answer by:
    1. Combining all retrieved context
    2. Generating a draft answer
    3. Self-checking for completeness
    4. Regenerating if needed
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    async def execute(
        self,
        question: str,
        planner_output: PlannerOutput,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        alignment_output: AlignmentOutput
    ) -> QueryResult:
        """
        Synthesize final answer from all retrieved information.

        Args:
            question: User's original question
            planner_output: Output from Planner Agent
            timeline_chunks: Retrieved timeline chunks
            document_chunks: Retrieved document chunks
            alignment_output: Output from Alignment Agent

        Returns:
            QueryResult with final answer and metadata
        """
        # Step 1: Generate draft answer
        draft_answer = await self._generate_answer(
            question,
            planner_output,
            timeline_chunks,
            document_chunks,
            alignment_output
        )

        # Step 2: Self-check for completeness
        needs_improvement, feedback = await self._self_check(
            question, draft_answer, planner_output
        )

        # Step 3: Regenerate if needed
        if needs_improvement:
            final_answer = await self._regenerate_answer(
                question,
                draft_answer,
                feedback,
                timeline_chunks,
                document_chunks,
                alignment_output
            )
        else:
            final_answer = draft_answer

        return QueryResult(
            answer=final_answer,
            timeline_chunks=timeline_chunks,
            document_chunks=document_chunks,
            dates_used=[],  # dates no longer surface by default
            confidence=0.85  # Could be computed based on retrieval scores
        )

    async def _generate_answer(
        self,
        question: str,
        planner_output: PlannerOutput,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        alignment_output: AlignmentOutput
    ) -> str:
        """
        Generate initial answer from context.
        """
        # Build context from all sources
        context = self._build_context(
            timeline_chunks, document_chunks, alignment_output
        )

        # Create synthesis prompt
        prompt = f"""You are a helpful AI assistant with access to a user's personal knowledge base.

User's Question: {question}

Retrieval Plan:
{planner_output.subtasks}

Retrieved Context:
{context}

Alignment Summary:
{alignment_output.alignment_summary}

Based on the above context, provide a clear, concise, and accurate answer to the user's question.
If the context doesn't contain enough information to fully answer the question, acknowledge this.
Cite specific dates or sources when relevant."""

        messages = [
            {"role": "system", "content": "You are a knowledgeable AI assistant helping answer questions based on retrieved context from a personal knowledge base."},
            {"role": "user", "content": prompt}
        ]

        answer = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )

        return answer

    async def _self_check(
        self,
        question: str,
        answer: str,
        planner_output: PlannerOutput
    ) -> tuple[bool, str]:
        """
        Check if the answer adequately addresses the question.

        Returns:
            Tuple of (needs_improvement, feedback)
        """
        check_prompt = f"""Evaluate if the following answer adequately addresses the question.

Question: {question}
Planned subtasks: {planner_output.subtasks}

Answer: {answer}

Does this answer:
1. Directly address the question?
2. Cover the key subtasks identified?
3. Acknowledge gaps if information is missing?

Respond in JSON format:
{{
  "adequate": true/false,
  "feedback": "brief feedback on what's missing or could be improved"
}}"""

        messages = [
            {"role": "system", "content": "You are an evaluator checking answer quality."},
            {"role": "user", "content": check_prompt}
        ]

        try:
            response = await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )

            result = json.loads(response)
            adequate = result.get("adequate", True)
            feedback = result.get("feedback", "")

            return (not adequate, feedback)

        except Exception as e:
            # If check fails, assume answer is adequate
            return (False, "")

    async def _regenerate_answer(
        self,
        question: str,
        draft_answer: str,
        feedback: str,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        alignment_output: AlignmentOutput
    ) -> str:
        """
        Regenerate answer based on feedback.
        """
        context = self._build_context(
            timeline_chunks, document_chunks, alignment_output
        )

        regenerate_prompt = f"""You previously generated this answer:

{draft_answer}

However, it had these issues:
{feedback}

Using the same context, generate an improved answer that addresses these concerns.

Context:
{context}

Question: {question}

Improved Answer:"""

        messages = [
            {"role": "system", "content": "You are a helpful AI assistant improving a previous answer based on feedback."},
            {"role": "user", "content": regenerate_prompt}
        ]

        improved_answer = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.7,
            max_tokens=600
        )

        return improved_answer

    def _build_context(
        self,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        alignment_output: AlignmentOutput
    ) -> str:
        """
        Build unified context string from all chunks.
        """
        # Use the merged context from alignment agent
        return alignment_output.merged_context
