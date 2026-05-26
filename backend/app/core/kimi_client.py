"""
Kimi (Moonshot AI) client — OpenAI-compatible API.
Base URL: https://api.moonshot.cn/v1
Used as the AI intelligence layer for scraping, validation, and discovery.
"""
import json
import os
from typing import Any, Optional
import httpx
import structlog

log = structlog.get_logger()

KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL_FAST = "moonshot-v1-8k"
KIMI_MODEL_LONG = "moonshot-v1-32k"


def _get_api_key() -> Optional[str]:
    """Read KIMI_API_KEY from environment or settings, whichever is available."""
    key = os.environ.get("KIMI_API_KEY")
    if key:
        return key
    try:
        from app.core.config import settings
        return settings.KIMI_API_KEY
    except Exception:
        return None


async def kimi_chat(
    messages: list[dict],
    model: str = KIMI_MODEL_FAST,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> Optional[str]:
    """Send a chat request to Kimi. Returns the assistant's text or None on failure."""
    api_key = _get_api_key()
    if not api_key:
        log.warning("KIMI_API_KEY not set — skipping AI call")
        return None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{KIMI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        log.warning("Kimi API call failed", error=str(e))
        return None


async def kimi_extract_json(
    prompt: str,
    context: str,
    model: str = KIMI_MODEL_FAST,
) -> Optional[dict | list]:
    """Ask Kimi to extract structured JSON from context. Returns parsed dict or None."""
    messages = [
        {
            "role": "system",
            "content": "You are a data extraction assistant. Always respond with valid JSON only, no markdown, no explanation.",
        },
        {
            "role": "user",
            "content": f"{prompt}\n\nContext:\n{context[:8000]}",
        },
    ]
    result = await kimi_chat(messages, model=model, temperature=0.1, max_tokens=512)
    if not result:
        return None
    try:
        cleaned = result.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        log.warning("Kimi returned invalid JSON", raw=result[:200])
        return None
