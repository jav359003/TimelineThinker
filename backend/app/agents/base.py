"""
Base agent class and common data structures.
"""
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import date
from abc import ABC, abstractmethod


@dataclass
class PlannerOutput:
    """
    Output from the Planner Agent.
    """
    temporal_scope: Optional[Dict[str, Any]]  # {"type": "date|range|none", "start": date, "end": date}
    topics: List[str]
    entities: List[str]
    subtasks: str  # Natural language description


@dataclass
class TimelineChunk:
    """
    A chunk retrieved from the timeline.
    """
    event_id: int
    text: str
    date: date
    event_type: str
    relevance_score: float


@dataclass
class DocumentChunk:
    """
    A chunk retrieved from documents.
    """
    event_id: int
    text: str
    source_title: str
    event_type: str
    relevance_score: float


@dataclass
class AlignmentOutput:
    """
    Output from the Alignment Agent.
    """
    aligned_pairs: List[tuple]  # List of (timeline_chunk, document_chunk, similarity_score)
    alignment_summary: str
    merged_context: str


@dataclass
class QueryResult:
    """
    Final result from the query pipeline.
    """
    answer: str
    timeline_chunks: List[TimelineChunk]
    document_chunks: List[DocumentChunk]
    dates_used: List[date]
    confidence: float


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """

    @abstractmethod
    async def execute(self, *args, **kwargs):
        """
        Execute the agent's primary function.
        """
        pass
