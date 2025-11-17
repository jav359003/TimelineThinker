"""
Alignment Agent: Aligns timeline and document chunks to find connections.
"""
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent, TimelineChunk, DocumentChunk, AlignmentOutput
from app.services.embedding_service import get_embedding_service
from app.services.llm_client import get_llm_client
from app.models.event import EventEmbedding


class AlignmentAgent(BaseAgent):
    """
    Alignment Agent computes relationships between timeline and document chunks.
    It identifies which document chunks relate to which timeline events and creates
    a unified context for the synthesizer.
    """

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.llm_client = get_llm_client()

    async def execute(
        self,
        db: Session,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        question: str
    ) -> AlignmentOutput:
        """
        Align timeline and document chunks.

        Args:
            db: Database session
            timeline_chunks: Timeline chunks from Timeline Retrieval Agent
            document_chunks: Document chunks from Document Retrieval Agent
            question: User's question for context

        Returns:
            AlignmentOutput with aligned pairs and summary
        """
        if not timeline_chunks and not document_chunks:
            return AlignmentOutput(
                aligned_pairs=[],
                alignment_summary="No relevant information found.",
                merged_context=""
            )

        # Step 1: Compute pairwise similarities
        aligned_pairs = await self._compute_alignments(
            db, timeline_chunks, document_chunks
        )

        # Step 2: Generate alignment summary
        alignment_summary = await self._generate_alignment_summary(
            aligned_pairs, timeline_chunks, document_chunks, question
        )

        # Step 3: Create merged context
        merged_context = self._create_merged_context(
            timeline_chunks, document_chunks, aligned_pairs
        )

        return AlignmentOutput(
            aligned_pairs=aligned_pairs,
            alignment_summary=alignment_summary,
            merged_context=merged_context
        )

    async def _compute_alignments(
        self,
        db: Session,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk]
    ) -> List[Tuple[TimelineChunk, DocumentChunk, float]]:
        """
        Compute pairwise similarity between timeline and document chunks.
        """
        if not timeline_chunks or not document_chunks:
            return []

        aligned_pairs = []

        # Get embeddings for all chunks
        timeline_embeddings = {}
        document_embeddings = {}

        # Fetch timeline embeddings
        for chunk in timeline_chunks:
            emb = db.query(EventEmbedding).filter(
                EventEmbedding.event_id == chunk.event_id
            ).first()
            if emb:
                timeline_embeddings[chunk.event_id] = emb.embedding

        # Fetch document embeddings
        for chunk in document_chunks:
            emb = db.query(EventEmbedding).filter(
                EventEmbedding.event_id == chunk.event_id
            ).first()
            if emb:
                document_embeddings[chunk.event_id] = emb.embedding

        # Compute similarities
        for t_chunk in timeline_chunks:
            for d_chunk in document_chunks:
                t_emb = timeline_embeddings.get(t_chunk.event_id)
                d_emb = document_embeddings.get(d_chunk.event_id)

                if t_emb is not None and d_emb is not None:
                    similarity = self.embedding_service.cosine_similarity(
                        t_emb, d_emb
                    )

                    # Only include pairs with meaningful similarity
                    if similarity > 0.6:
                        aligned_pairs.append((t_chunk, d_chunk, similarity))

        # Sort by similarity
        aligned_pairs.sort(key=lambda x: x[2], reverse=True)

        # Return top alignments
        return aligned_pairs[:5]

    async def _generate_alignment_summary(
        self,
        aligned_pairs: List[Tuple[TimelineChunk, DocumentChunk, float]],
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        question: str
    ) -> str:
        """
        Generate a natural language summary of how timeline and documents relate.
        """
        if not aligned_pairs and not timeline_chunks and not document_chunks:
            return "No relevant information found."

        # Create a concise summary of relationships
        summary_parts = []

        if timeline_chunks:
            dates = list(set(chunk.date for chunk in timeline_chunks))
            dates.sort()
            date_str = ", ".join(d.strftime("%b %d") for d in dates[:3])
            summary_parts.append(f"Found timeline events from {date_str}")

        if document_chunks:
            sources = list(set(chunk.source_title for chunk in document_chunks))
            source_str = ", ".join(sources[:3])
            summary_parts.append(f"Found relevant documents: {source_str}")

        if aligned_pairs:
            summary_parts.append(
                f"Identified {len(aligned_pairs)} strong connections between timeline and documents"
            )

        return ". ".join(summary_parts) + "."

    def _create_merged_context(
        self,
        timeline_chunks: List[TimelineChunk],
        document_chunks: List[DocumentChunk],
        aligned_pairs: List[tuple]
    ) -> str:
        """
        Create a unified context string for the synthesizer.
        """
        context_parts = []

        # Add timeline context
        if timeline_chunks:
            context_parts.append("=== TIMELINE EVENTS ===")
            for chunk in timeline_chunks[:5]:
                context_parts.append(
                    f"[{chunk.date.strftime('%Y-%m-%d')}] {chunk.text[:300]}"
                )

        # Add document context
        if document_chunks:
            context_parts.append("\n=== RELEVANT DOCUMENTS ===")
            for chunk in document_chunks[:5]:
                context_parts.append(
                    f"[{chunk.source_title}] {chunk.text[:300]}"
                )

        # Add aligned pairs if they exist
        if aligned_pairs:
            context_parts.append("\n=== KEY CONNECTIONS ===")
            for t_chunk, d_chunk, score in aligned_pairs[:3]:
                context_parts.append(
                    f"Timeline ({t_chunk.date}) relates to Document ({d_chunk.source_title}): "
                    f"similarity {score:.2f}"
                )

        return "\n\n".join(context_parts)
