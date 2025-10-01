"""LLM-powered summarization service."""
from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class SummarizationService:
    """Encapsulates LLM prompt/response handling."""

    def __init__(self, client: Optional[AsyncOpenAI] = None):
        if client:
            self._client = client
        else:
            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    async def summarize(self, text: str, max_words: int = 60) -> str:
        """Call the LLM to produce a concise summary."""

        prompt = (
            "Summarize the following government update in no more than"
            f" {max_words} words. Focus on the action, affected parties, and timeframe.\n\n{text}"
        )
        response = await self._client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": "You are an expert policy analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()


async def get_summarization_service() -> SummarizationService:
    """Dependency injection helper."""

    return SummarizationService()
