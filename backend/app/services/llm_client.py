"""
Unified LLM client abstraction supporting OpenAI and Anthropic.
Provides a consistent interface for chat completions across providers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, AsyncIterator
from app.config import get_settings
import openai
import anthropic

settings = get_settings()


class BaseLLMClient(ABC):
    """
    Abstract base class for LLM clients.
    Defines the interface that all provider-specific clients must implement.
    """

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Yields:
            Text chunks as they're generated
        """
        pass


class OpenAIClient(BaseLLMClient):
    """
    OpenAI implementation of LLM client.
    """

    def __init__(self, api_key: str, model: str):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a chat completion using OpenAI API.
        """
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion using OpenAI API.
        """
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicClient(BaseLLMClient):
    """
    Anthropic (Claude) implementation of LLM client.
    """

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def _convert_messages(self, messages: List[Dict[str, str]]) -> tuple:
        """
        Convert OpenAI-style messages to Anthropic format.
        Anthropic requires system message separate from conversation messages.
        """
        system_message = None
        conversation_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                conversation_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        return system_message, conversation_messages

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """
        Generate a chat completion using Anthropic API.
        """
        system_message, conversation_messages = self._convert_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_message:
            kwargs["system"] = system_message

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion using Anthropic API.
        """
        system_message, conversation_messages = self._convert_messages(messages)

        kwargs = {
            "model": self.model,
            "messages": conversation_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_message:
            kwargs["system"] = system_message

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text


class LLMClientFactory:
    """
    Factory class to create the appropriate LLM client based on configuration.
    """

    @staticmethod
    def create_client() -> BaseLLMClient:
        """
        Create and return an LLM client based on settings.

        Returns:
            Configured LLM client instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = settings.llm_provider.lower()

        if provider == "openai":
            return OpenAIClient(
                api_key=settings.openai_api_key,
                model=settings.llm_model
            )
        elif provider == "anthropic":
            return AnthropicClient(
                api_key=settings.anthropic_api_key,
                model=settings.llm_model
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")


# Global client instance
_llm_client: Optional[BaseLLMClient] = None


def get_llm_client() -> BaseLLMClient:
    """
    Get or create the global LLM client instance.

    Returns:
        Singleton LLM client
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClientFactory.create_client()
    return _llm_client
