"""
Session service for tracking per-day interactions and generating summaries.
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.session import SessionInteraction, SessionSource
from app.models.source import Source
from app.services.llm_client import get_llm_client


class SessionService:
    """Manages session interactions, sources, and summaries."""

    def __init__(self):
        self.llm_client = get_llm_client()

    def log_interaction(
        self,
        db: Session,
        user_id: int,
        question: str,
        answer: str,
        source_id: Optional[int],
        session_date: Optional[date] = None,
    ) -> SessionInteraction:
        """
        Persist a question/answer pair and ensure the source is tracked for the session.
        """
        if session_date is None:
            session_date = date.today()

        interaction = SessionInteraction(
            user_id=user_id,
            source_id=source_id,
            question=question,
            answer=answer,
            session_date=session_date,
        )
        db.add(interaction)

        if source_id:
            self.ensure_session_source(db, user_id, source_id, session_date)

        db.commit()
        db.refresh(interaction)
        return interaction

    def ensure_session_source(
        self,
        db: Session,
        user_id: int,
        source_id: int,
        session_date: date,
    ) -> SessionSource:
        """
        Ensure a source is marked as part of a session.
        """
        session_source = (
            db.query(SessionSource)
            .filter(
                SessionSource.user_id == user_id,
                SessionSource.source_id == source_id,
                SessionSource.session_date == session_date,
            )
            .first()
        )

        if session_source:
            if session_source.removed_at is not None:
                session_source.removed_at = None
                db.add(session_source)
            return session_source

        session_source = SessionSource(
            user_id=user_id,
            source_id=source_id,
            session_date=session_date,
        )
        db.add(session_source)
        return session_source

    def remove_session_source(
        self,
        db: Session,
        user_id: int,
        source_id: int,
        session_date: date,
    ) -> None:
        """
        Soft-remove a source from today's session.
        """
        session_source = (
            db.query(SessionSource)
            .filter(
                SessionSource.user_id == user_id,
                SessionSource.source_id == source_id,
                SessionSource.session_date == session_date,
            )
            .first()
        )

        if session_source:
            session_source.removed_at = datetime.utcnow()
            db.add(session_source)
            db.commit()

    def get_session_snapshot(
        self,
        db: Session,
        user_id: int,
        session_date: date,
        interaction_limit: int = 20,
    ) -> dict:
        """
        Return the current session state, including sources and recent interactions.
        """
        sources = (
            db.query(SessionSource, Source)
            .join(Source, SessionSource.source_id == Source.id)
            .filter(
                SessionSource.user_id == user_id,
                SessionSource.session_date == session_date,
                SessionSource.removed_at.is_(None),
            )
            .order_by(SessionSource.added_at.asc())
            .all()
        )

        interactions = (
            db.query(SessionInteraction)
            .filter(
                SessionInteraction.user_id == user_id,
                SessionInteraction.session_date == session_date,
            )
            .order_by(SessionInteraction.created_at.desc())
            .limit(interaction_limit)
            .all()
        )

        sources_payload = [
            {
                "id": src.id,
                "source_id": src.source_id,
                "title": source.title,
                "source_type": source.source_type,
                "uri": source.uri,
                "added_at": src.added_at,
            }
            for src, source in sources
        ]

        interactions_payload = [
            {
                "id": interaction.id,
                "question": interaction.question,
                "answer": interaction.answer,
                "source_id": interaction.source_id,
                "created_at": interaction.created_at,
            }
            for interaction in interactions
        ]

        return {
            "date": session_date,
            "sources": sources_payload,
            "interactions": interactions_payload,
        }

    async def summarize_interactions(self, interactions: list) -> Optional[str]:
        """
        Use the LLM to summarize the session interactions.
        """
        try:
            prompt_lines = ["Summarize the user's day based on these interactions:"]
            for interaction in interactions[-10:]:
                prompt_lines.append(f"Q: {interaction['question']}")
                prompt_lines.append(f"A: {interaction['answer']}")

            prompt = "\n".join(prompt_lines)
            messages = [
                {
                    "role": "system",
                    "content": "You are an assistant summarizing a user's personal knowledge session.",
                },
                {"role": "user", "content": prompt},
            ]
            return await self.llm_client.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=300,
            )
        except Exception:
            return None

    def clear_session(
        self,
        db: Session,
        user_id: int,
        session_date: date
    ) -> None:
        """
        Remove all session data for a given day.
        """
        db.query(SessionInteraction).filter(
            SessionInteraction.user_id == user_id,
            SessionInteraction.session_date == session_date
        ).delete()

        db.query(SessionSource).filter(
            SessionSource.user_id == user_id,
            SessionSource.session_date == session_date
        ).delete()

        db.commit()


_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
