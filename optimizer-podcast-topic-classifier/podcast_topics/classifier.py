"""Classify one episode blurb with a chat model."""

import openai

from .prompts import BASELINE_SYSTEM, MODEL, USER_TEMPLATE

_client: openai.OpenAI | None = None


def get_client() -> openai.OpenAI:
    """Build the OpenAI client on first use so importing never needs a key."""
    global _client
    if _client is None:
        _client = openai.OpenAI()
    return _client


def classify(episode: str, system: str = BASELINE_SYSTEM) -> str:
    """Ask the model for the topic of a single episode blurb."""
    response = get_client().chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": USER_TEMPLATE.format(episode=episode)},
        ],
    )
    return response.choices[0].message.content or ""
