"""The triage agent: a BeeAI ReAct agent, its prompt, and the parser for its answer."""
import re

from beeai_framework.agents.react import ReActAgent
from beeai_framework.backend import ChatModel
from beeai_framework.memory import UnconstrainedMemory

from tools import lookup_safe_range, lookup_tank

MODEL = "openai:gpt-4o-mini"
SEVERITIES = ("ok", "watch", "urgent")

INSTRUCTIONS = """You triage water-quality alerts for the fish room at Brightwater Aquatics.

For the alert below:
1. Call lookup_tank to learn the tank type and what lives in it.
2. Call lookup_safe_range with that tank type and the alert's parameter. Never judge a reading without it.
3. Decide severity: "ok" if inside the safe band, "watch" if outside it but not past an urgent threshold,
   "urgent" if past an urgent threshold. Then give one concrete action for the keeper.

Format your final answer exactly like this:
Severity: <ok | watch | urgent>
Why: <one sentence citing the reading and the range>
Action: <one concrete step for the keeper>
Notify: <keeper name>"""


def build_prompt(alert: dict) -> str:
    return (
        f"{INSTRUCTIONS}\n\nAlert: tank {alert['tank_id']} reports "
        f"{alert['parameter']} = {alert['reading']}. Note: {alert['note']}"
    )


def parse_triage(text: str) -> dict:
    """Pull the four labelled lines out of the agent's final answer; missing ones come back as None."""
    out: dict = {}
    for label in ("Severity", "Why", "Action", "Notify"):
        m = re.search(rf"^{label}:\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
        out[label.lower()] = m.group(1).strip() if m else None
    sev = (out["severity"] or "").lower()
    out["severity"] = sev if sev in SEVERITIES else None
    return out


def make_agent(llm: ChatModel | None = None) -> ReActAgent:
    llm = llm or ChatModel.from_name(MODEL)
    # A fresh agent and memory per alert keeps every alert an independent trace in Opik.
    return ReActAgent(llm=llm, tools=[lookup_tank, lookup_safe_range], memory=UnconstrainedMemory())


async def triage_alert(alert: dict, llm: ChatModel | None = None) -> dict:
    # agent.run() is the root of the trace; each ReAct turn becomes an iteration span under it.
    result = await make_agent(llm).run(build_prompt(alert), max_iterations=8, max_retries_per_step=3, total_max_retries=6)
    return parse_triage(result.last_message.text)
