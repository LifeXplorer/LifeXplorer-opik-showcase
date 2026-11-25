"""The three activities: screen (LLM), check the budget ledger (flaky), draft the letter (LLM)."""
import json
import os

from dotenv import find_dotenv, load_dotenv
from openai import AsyncOpenAI
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from temporalio import activity

from models import Application, BudgetCheck, Screening

load_dotenv(find_dotenv())
# Always talk to the public OpenAI API, even if a local proxy URL is exported.
os.environ.pop("OPENAI_BASE_URL", None)

MODEL = "gpt-4o-mini"
tracer = trace.get_tracer("grant-activities")

# Canned fund ledger: what is left in each category this quarter.
LEDGER = {"garden": 5000, "youth": 6000, "arts": 3500, "mobility": 8000, "other": 2000}

APPROVE_MIN_SCORE = 3


async def chat(name: str, system: str, user: str, *, json_mode: bool = False) -> str:
    # A child span of the current activity span, so the model call nests inside the RunActivity
    # attempt that made it. The gen_ai.* attributes are what Opik reads to type the span as an
    # llm span and to compute token usage and cost; without them it would be a plain span.
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    with tracer.start_as_current_span(name) as span:
        client = AsyncOpenAI()
        response = await client.chat.completions.create(
            model=MODEL,
            messages=messages,
            **({"response_format": {"type": "json_object"}} if json_mode else {}),
        )
        content = response.choices[0].message.content or ""
        usage = response.usage
        span.set_attributes(
            {
                "gen_ai.operation.name": "chat",
                "gen_ai.provider.name": "openai",
                "gen_ai.request.model": MODEL,
                "gen_ai.response.model": response.model,
                "gen_ai.usage.input_tokens": usage.prompt_tokens,
                "gen_ai.usage.output_tokens": usage.completion_tokens,
                "input.value": json.dumps({"messages": messages}),  # shown as the span input
                "output.value": content,  # shown as the span output
                # opik.metadata (JSON) is merged into the span metadata; other unmapped attributes would land in the input
                "opik.metadata": json.dumps({"process": "worker", "pid": os.getpid()}),
            }
        )
        span.set_status(Status(StatusCode.OK))
        return content


def parse_screening(raw: str) -> Screening:
    """Turn the model's JSON into a Screening, clamping the score and normalising the category."""
    data = json.loads(raw)
    category = str(data.get("category", "other")).lower()
    if category not in LEDGER:
        category = "other"
    score = max(1, min(5, int(data.get("fit_score", 1))))
    return Screening(
        category=category,
        requested_amount=int(data.get("requested_amount", 0)),
        fit_score=score,
        summary=str(data.get("summary", "")),
    )


def decide(screening: Screening, budget: BudgetCheck) -> str:
    """Approve only a well-fitting proposal the category fund can cover."""
    if screening.fit_score >= APPROVE_MIN_SCORE and budget.affordable:
        return "approved"
    return "declined"


@activity.defn
async def screen_application(application: Application) -> Screening:
    raw = await chat(
        "screen-application",
        "You screen community-grant applications for a neighbourhood fund. "
        "Reply with JSON: {\"category\": \"garden\"|\"youth\"|\"arts\"|\"mobility\"|\"other\", "
        "\"requested_amount\": integer dollars, \"fit_score\": integer 1-5 for how clearly the "
        "proposal serves the neighbourhood with a concrete plan, \"summary\": one sentence}.",
        f"Applicant: {application.applicant}\nProposal: {application.proposal}",
        json_mode=True,
    )
    return parse_screening(raw)


@activity.defn
async def check_budget(screening: Screening) -> BudgetCheck:
    # Deliberate transient failure: the first attempt always fails, like a flaky ledger service.
    if activity.info().attempt == 1:
        raise RuntimeError("Ledger service unavailable: connection reset (transient, succeeds on retry)")
    remaining = LEDGER[screening.category]
    return BudgetCheck(
        category=screening.category,
        requested_amount=screening.requested_amount,
        remaining_before=remaining,
        affordable=screening.requested_amount <= remaining,
    )


@activity.defn
async def draft_letter(application: Application, screening: Screening, budget: BudgetCheck, decision: str) -> str:
    return await chat(
        "draft-decision-letter",
        "You write short, warm decision letters for a neighbourhood grant fund. State the "
        "decision plainly. If declined, give the concrete reason (fit or budget) and invite "
        "a smaller or reworked request. Under 110 words, no subject line, no placeholders; "
        "sign off as The Neighbourhood Fund Committee.",
        json.dumps(
            {
                "applicant": application.applicant,
                "decision": decision,
                "summary": screening.summary,
                "requested_amount": budget.requested_amount,
                "fund_remaining": budget.remaining_before,
                "fit_score": screening.fit_score,
            }
        ),
    )
