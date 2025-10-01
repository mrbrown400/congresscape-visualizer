"""Vector embedding helpers using OpenAI."""
from __future__ import annotations

from typing import Optional

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class EmbeddingService:
    def __init__(self, client: Optional[AsyncOpenAI] = None, model: str = "text-embedding-3-large"):
        if client:
            self._client = client
        else:
            if not settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = model

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
    async def embed(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding


async def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
