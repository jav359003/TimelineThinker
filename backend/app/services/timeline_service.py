"""
Timeline service for generating daily and weekly summaries.
"""
from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import json

from app.models.event import Event
from app.models.timeline import DailyTimeline, WeeklyTimeline
from app.services.llm_client import get_llm_client


class TimelineService:
    """
    Service for generating and managing daily/weekly timeline summaries.
    """

    def __init__(self):
        self.llm_client = get_llm_client()

    async def generate_daily_summary(
        self,
        db: Session,
        user_id: int,
        target_date: date
    ) -> Optional[DailyTimeline]:
        """
        Generate or update a daily summary for a specific date.

        Args:
            db: Database session
            user_id: User ID
            target_date: Date to summarize

        Returns:
            DailyTimeline object
        """
        # Fetch all events for this day
        events = db.query(Event).filter(
            and_(
                Event.user_id == user_id,
                Event.date == target_date
            )
        ).order_by(Event.timestamp).all()

        if not events:
            return None

        # Aggregate event texts
        event_texts = [f"- {event.raw_text[:200]}" for event in events[:20]]  # Limit to first 20
        combined_text = "\n".join(event_texts)

        # Generate summary using LLM
        prompt = f"""Summarize the following events from {target_date.strftime('%B %d, %Y')}.
Create a concise 2-3 sentence summary of the main activities and topics.

Events:
{combined_text}

Summary:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise daily summaries."},
            {"role": "user", "content": prompt}
        ]

        summary_text = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=200
        )

        # Extract metadata (top entities, topics)
        event_types = {}
        for event in events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

        metadata = {
            "event_types": event_types,
            "total_events": len(events)
        }

        # Check if daily timeline already exists
        daily_timeline = db.query(DailyTimeline).filter(
            and_(
                DailyTimeline.user_id == user_id,
                DailyTimeline.date == target_date
            )
        ).first()

        if daily_timeline:
            # Update existing
            daily_timeline.summary_text = summary_text
            daily_timeline.event_count = len(events)
            daily_timeline.timeline_metadata = json.dumps(metadata)
            daily_timeline.updated_at = datetime.utcnow()
        else:
            # Create new
            daily_timeline = DailyTimeline(
                user_id=user_id,
                date=target_date,
                summary_text=summary_text,
                event_count=len(events),
                timeline_metadata=json.dumps(metadata)
            )
            db.add(daily_timeline)

        db.commit()
        db.refresh(daily_timeline)

        return daily_timeline

    async def generate_weekly_summary(
        self,
        db: Session,
        user_id: int,
        week_start_date: date
    ) -> Optional[WeeklyTimeline]:
        """
        Generate or update a weekly summary.

        Args:
            db: Database session
            user_id: User ID
            week_start_date: Start date of the week (Monday)

        Returns:
            WeeklyTimeline object
        """
        week_end_date = week_start_date + timedelta(days=6)

        # Fetch daily summaries for this week
        daily_summaries = db.query(DailyTimeline).filter(
            and_(
                DailyTimeline.user_id == user_id,
                DailyTimeline.date >= week_start_date,
                DailyTimeline.date <= week_end_date
            )
        ).order_by(DailyTimeline.date).all()

        if not daily_summaries:
            return None

        # Aggregate daily summaries
        daily_texts = [
            f"{summary.date.strftime('%A, %B %d')}: {summary.summary_text}"
            for summary in daily_summaries
        ]
        combined_text = "\n\n".join(daily_texts)

        # Generate weekly summary
        prompt = f"""Summarize the following week ({week_start_date.strftime('%B %d')} - {week_end_date.strftime('%B %d, %Y')}).
Create a concise paragraph highlighting the main themes, accomplishments, and patterns.

Daily summaries:
{combined_text}

Weekly summary:"""

        messages = [
            {"role": "system", "content": "You are a helpful assistant that creates concise weekly summaries."},
            {"role": "user", "content": prompt}
        ]

        summary_text = await self.llm_client.chat_completion(
            messages=messages,
            temperature=0.5,
            max_tokens=300
        )

        total_events = sum(summary.event_count for summary in daily_summaries)

        # Check if weekly timeline exists
        weekly_timeline = db.query(WeeklyTimeline).filter(
            and_(
                WeeklyTimeline.user_id == user_id,
                WeeklyTimeline.week_start_date == week_start_date
            )
        ).first()

        if weekly_timeline:
            # Update existing
            weekly_timeline.summary_text = summary_text
            weekly_timeline.event_count = total_events
            weekly_timeline.updated_at = datetime.utcnow()
        else:
            # Create new
            weekly_timeline = WeeklyTimeline(
                user_id=user_id,
                week_start_date=week_start_date,
                summary_text=summary_text,
                event_count=total_events
            )
            db.add(weekly_timeline)

        db.commit()
        db.refresh(weekly_timeline)

        return weekly_timeline

    def get_week_start(self, target_date: date) -> date:
        """
        Get the Monday of the week containing target_date.

        Args:
            target_date: Any date in the week

        Returns:
            Date of the Monday
        """
        days_since_monday = target_date.weekday()
        week_start = target_date - timedelta(days=days_since_monday)
        return week_start

    async def update_timelines_for_date(
        self,
        db: Session,
        user_id: int,
        target_date: date
    ):
        """
        Update both daily and weekly timelines for a given date.

        Args:
            db: Database session
            user_id: User ID
            target_date: Date to update timelines for
        """
        # Update daily timeline
        await self.generate_daily_summary(db, user_id, target_date)

        # Update weekly timeline
        week_start = self.get_week_start(target_date)
        await self.generate_weekly_summary(db, user_id, week_start)


def get_timeline_service() -> TimelineService:
    """
    Get timeline service instance.

    Returns:
        TimelineService instance
    """
    return TimelineService()
