"""LLM-based semantic verification of citations."""
from __future__ import annotations

import json
import os
from typing import Literal

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


PROMPT = """You verify citations. Given a CLAIM and the CONTENT of a source page,
decide whether the source genuinely supports the claim.

Return JSON with fields:
- support: one of "supports", "partial", "unrelated", "contradicts"
- reason: one sentence explaining the decision
- evidence: the most relevant phrase (<=200 chars) from the content

CLAIM: {claim}

CONTENT (truncated):
{content}

Respond with JSON only, no prose."""


def verify_semantic(claim: str, content: str) -> dict:
    """Use Gemini to evaluate whether content supports the claim."""
    if not GENAI_AVAILABLE:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")

    # Prefer Vertex AI if configured, fall back to Gemini API
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        client = genai.Client(
            vertexai=True,
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "europe-west1"),
        )
    else:
        client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    # Truncate content to stay within reasonable token budget
    truncated = content[:8000]
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=PROMPT.format(claim=claim, content=truncated),
    )
    text = response.text.strip()
    # Strip code fences if the model added them
    if text.startswith("```"):
        text = text.split("```")[1].removeprefix("json").strip()
    return json.loads(text)
