"""Optional LLM client (any OpenAI-compatible API, e.g. OpenRouter free models).

Everything the model returns is parsed as JSON and validated with Pydantic. If the call
fails or the JSON is invalid, the caller falls back to the rule engine.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Protocol

import httpx

from .config import settings

log = logging.getLogger("termguard.llm")


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str, model: str, timeout: float = 60.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, system: str, user: str) -> str:
        resp = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "X-Title": "TermGuard"},
            json={
                "model": self.model,
                "temperature": 0,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def default_client() -> LLMClient | None:
    if not settings.llm_enabled:
        return None
    return OpenAICompatibleClient(settings.llm_api_key, settings.llm_base_url, settings.llm_model)


def parse_json(text: str) -> dict:
    """Pull the first JSON object out of a model reply (handles ```json fences)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = fenced.group(1) if fenced else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)


ANALYSIS_SYSTEM = """You review clauses from Indian rental agreements and job offer letters for a student.
You give information, not legal advice.
For each clause, decide which of the CANDIDATE checklist items truly apply. Most clauses are fine;
only report an item if the clause really contains that risk.
Return ONLY JSON: {"results": [{"clause_id": "...", "findings": [{"checklist_id": "...",
"risk": "high|medium|low", "explanation": "...", "quote": "...", "question": "..."}]}]}
Rules:
- quote MUST be copied word for word from that clause (one sentence or less). Never rephrase it.
- explanation: 2-3 short sentences, plain English, no legal jargon, say what it means for the user.
- question: one question the user can ask the owner or HR.
- Placeholders like [PERSON_1] are redacted personal details; keep them as they are.
- Use only checklist_id values from that clause's candidates."""

TRANSLATE_SYSTEM = """Translate each English explanation into simple, everyday {language}.
Keep any text in [SQUARE_BRACKETS] unchanged. Return ONLY JSON: {{"items": [{{"id": "...", "text": "..."}}]}}"""

SPLIT_SYSTEM = """You group numbered paragraphs of a contract into clauses.
Return ONLY JSON: {"clauses": [{"title": "short title", "paragraphs": [0, 1]}]}.
Every paragraph index must appear exactly once, in order."""
