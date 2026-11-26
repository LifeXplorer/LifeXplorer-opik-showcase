"""Classify one episode blurb with a chat model."""

import openai
import opik
from opik.integrations.openai import track_openai

from .prompts import BASELINE_SYSTEM, MODEL, USER_TEMPLATE

PROJECT_NAME = "optimizer-podcast-topic-classifier"

_client: openai.OpenAI | None = None


def get_client() -> openai.OpenAI:
    """Build the OpenAI client on first use so importing never needs a key."""
    global _client
    if _client is None:
        # track_openai wraps the client: every completion becomes an llm span with
        # model, messages, token usage and cost, filed under the project below.
        _client = track_openai(openai.OpenAI(), project_name=PROJECT_NAME)
    return _client


# @track opens one trace per episode (general span) with the blurb as input and the
# topic as output; the wrapped completion nests inside it as an llm span.
@opik.track(name="classify_episode", project_name=PROJECT_NAME)
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
