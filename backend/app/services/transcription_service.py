"""
Audio transcription service using OpenAI Whisper API.
"""
from typing import Tuple
import openai
import io
from app.config import get_settings

settings = get_settings()


class TranscriptionService:
    """
    Service for transcribing audio files to text using Whisper API.
    """

    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

    async def transcribe_audio(
        self,
        audio_content: bytes,
        filename: str
    ) -> Tuple[str, dict]:
        """
        Transcribe audio file to text.

        Args:
            audio_content: Binary audio file content
            filename: Original filename (for format detection)

        Returns:
            Tuple of (transcribed_text, metadata_dict)
        """
        try:
            # Create file-like object for API
            audio_file = io.BytesIO(audio_content)
            audio_file.name = filename

            # Call Whisper API
            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )

            # Extract text and metadata
            text = transcript.text
            metadata = {
                "duration": getattr(transcript, 'duration', None),
                "language": getattr(transcript, 'language', None),
                "file_type": "audio"
            }

            return text, metadata

        except Exception as e:
            raise ValueError(f"Failed to transcribe audio: {str(e)}")

    async def transcribe_audio_with_timestamps(
        self,
        audio_content: bytes,
        filename: str
    ) -> Tuple[str, list, dict]:
        """
        Transcribe audio with word-level timestamps.

        Args:
            audio_content: Binary audio file content
            filename: Original filename

        Returns:
            Tuple of (full_text, segments_list, metadata_dict)
        """
        try:
            audio_file = io.BytesIO(audio_content)
            audio_file.name = filename

            transcript = await self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )

            text = transcript.text
            segments = getattr(transcript, 'segments', [])

            metadata = {
                "duration": getattr(transcript, 'duration', None),
                "language": getattr(transcript, 'language', None),
                "segment_count": len(segments),
                "file_type": "audio"
            }

            return text, segments, metadata

        except Exception as e:
            raise ValueError(f"Failed to transcribe audio with timestamps: {str(e)}")


def get_transcription_service() -> TranscriptionService:
    """
    Get transcription service instance.

    Returns:
        TranscriptionService instance
    """
    return TranscriptionService()
