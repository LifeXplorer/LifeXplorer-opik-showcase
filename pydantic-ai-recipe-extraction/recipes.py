"""The RecipeCard agent, with its spans exported to Opik over OpenTelemetry."""

import os
from pathlib import Path
from typing import Any, Optional

from dotenv import find_dotenv, load_dotenv

PROJECT_NAME = "pydantic-ai-recipe-extraction"

# Provider keys come from a .env found by walking up from this folder.
load_dotenv(find_dotenv(usecwd=False) or find_dotenv(str(Path(__file__).parent / ".env")))


def configure_opik_otel() -> None:
    """Point the OTel exporter at Opik before logfire starts.

    Without these variables the spans are produced but go nowhere, and the
    project stays empty. projectName routes the traces to this example's project.
    """
    from opik.config import OpikConfig  # reads env vars and ~/.opik.config

    cfg = OpikConfig()
    base = (cfg.url_override or "https://www.comet.com/opik/api").rstrip("/")
    headers = [f"Comet-Workspace={cfg.workspace}", f"projectName={PROJECT_NAME}"]
    if cfg.api_key:  # local self-hosted Opik needs no Authorization header
        headers.insert(0, f"Authorization={cfg.api_key}")

    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{base}/v1/private/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = ",".join(headers)
    os.environ["OTEL_METRICS_EXPORTER"] = "none"


configure_opik_otel()

import logfire  # noqa: E402
import opik  # noqa: E402
from opik import opik_context  # noqa: E402
from opik.integrations.otel import OpikSpanProcessor  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from pydantic_ai import Agent  # noqa: E402

from grounding import find_ungrounded  # noqa: E402

# OpikSpanProcessor attaches the OTel spans to the surrounding @opik.track
# trace, so each extraction is ONE trace instead of loose agent spans.
logfire.configure(
    send_to_logfire=False,
    console=False,  # keep the terminal quiet; spans still go to Opik
    inspect_arguments=False,
    additional_span_processors=[OpikSpanProcessor()],
)
# instrument_pydantic_ai makes every agent run emit invoke_agent / chat spans
# (with model, tokens and the typed output) that the processor ships to Opik.
logfire.instrument_pydantic_ai()


class Ingredient(BaseModel):
    name: str
    quantity: Optional[str] = Field(None, description="Amount with unit as written, e.g. '2 cups'; null if no amount is given")


class RecipeCard(BaseModel):
    """A recipe card; every optional field stays null unless the note states it."""

    title: str
    credit: Optional[str] = Field(None, description="Who the recipe is from, if the note says")
    servings: Optional[int] = None
    prep_minutes: Optional[int] = None
    cook_minutes: Optional[int] = None
    oven_temp_c: Optional[int] = Field(None, description="Oven temperature in Celsius, only if an oven is used")
    ingredients: list[Ingredient]
    steps: list[str]


SYSTEM_PROMPT = (
    "You turn messy home-cook notes into a clean recipe card. Use only what "
    "the note says: if an amount, time, temperature or serving count is not "
    "written, leave it null. Never add ingredients or numbers the note lacks, "
    "and skip anything the note says not to use."
)


def build_agent(model: Any = "openai:gpt-4o-mini") -> Agent:
    return Agent(model, output_type=RecipeCard, system_prompt=SYSTEM_PROMPT)


agent = build_agent()


# @opik.track opens the parent trace (input = the note, output = the card);
# the OTel spans from the agent run nest under it.
@opik.track(project_name=PROJECT_NAME, name="extract_recipe")
def extract_recipe(text: str) -> dict[str, Any]:
    result = agent.run_sync(text)
    card = result.output.model_dump()
    problems = find_ungrounded(card, text)
    # A feedback score on the trace: 1.0 = every value traces back to the note.
    # Shows as a column in the traces table, so invented values are filterable.
    opik_context.update_current_trace(
        feedback_scores=[
            {
                "name": "grounded",
                "value": 0.0 if problems else 1.0,
                "reason": "; ".join(problems) or "all values found in the note",
            }
        ]
    )
    return card
