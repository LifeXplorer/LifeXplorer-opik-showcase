"""Insurance-claims triage on the OpenAI Agents SDK.

A triage agent hands each claim to an auto or property specialist. The
specialists call function tools backed by a small fictional policy file.
"""

import json
import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

from agents import Agent, Runner, function_tool

import claims_core

MODEL = "gpt-4o-mini"


@function_tool
def lookup_policy(policy_id: str) -> str:
    """Look up a policy: holder, kind, deductible, limit, active flag."""
    return json.dumps(claims_core.lookup_policy(policy_id))


@function_tool
def estimate_payout(policy_id: str, damage_usd: float) -> str:
    """Estimate the payout for a damage amount under a policy."""
    return json.dumps(claims_core.estimate_payout(policy_id, damage_usd))


@function_tool
def open_claim(policy_id: str, summary: str) -> str:
    """Open a claim on a policy and return the claim id."""
    return json.dumps(claims_core.open_claim(policy_id, summary))


auto_agent = Agent(
    name="Auto Claims Agent",
    handoff_description="Vehicle collisions, theft, and damage to cars.",
    instructions=(
        "You handle auto claims. Look up the policy first, estimate the "
        "payout when a damage amount is given, and open the claim only "
        "when the customer asks. Keep replies to three sentences."
    ),
    model=MODEL,
    tools=[lookup_policy, estimate_payout, open_claim],
)

property_agent = Agent(
    name="Property Claims Agent",
    handoff_description="Home damage: water, fire, storm, break-ins.",
    instructions=(
        "You handle home and property claims. Look up the policy first, "
        "estimate the payout when a damage amount is given, and open the "
        "claim only when the customer asks. Keep replies to three sentences."
    ),
    model=MODEL,
    tools=[lookup_policy, estimate_payout, open_claim],
)

triage_agent = Agent(
    name="Claims Triage Agent",
    instructions=(
        "You are the front desk of an insurance claims line. Hand every "
        "claim to the right specialist: cars go to auto, houses and "
        "belongings go to property. Never answer the claim yourself."
    ),
    model=MODEL,
    handoffs=[auto_agent, property_agent],
)

# Each conversation is several turns on one claim, with the specialist
# we expect triage to pick.
CONVERSATIONS = {
    "fender-bender": {
        "expected": "Auto Claims Agent",
        "turns": [
            "Hi, I'm Marta Okonkwo, policy POL-1001. Someone backed into my "
            "car in a parking lot, about $1,800 in damage. What would I get?",
            "Okay, please open the claim.",
        ],
    },
    "burst-pipe": {
        "expected": "Property Claims Agent",
        "turns": [
            "This is Daniel Reyes, policy POL-2002. A pipe burst in the "
            "kitchen and the floor is ruined, roughly $9,500 of damage.",
            "Open the claim for me please.",
        ],
    },
    "lapsed-policy": {
        "expected": "Auto Claims Agent",
        "turns": [
            "Priya Lindqvist, POL-3003. My car was stolen last night. "
            "Can you open a claim?",
        ],
    },
}


def run_demo() -> list[dict]:
    rows = []
    for name, spec in CONVERSATIONS.items():
        thread_id = f"{name}-{uuid.uuid4().hex[:8]}"
        print(f"\n=== {name} (thread {thread_id}) ===")
        history = []
        for message in spec["turns"]:
            print(f"\nCustomer: {message}")
            history.append({"role": "user", "content": message})
            result = Runner.run_sync(triage_agent, history)
            print(f"{result.last_agent.name}: {result.final_output}")
            history = result.to_input_list()
        rows.append({"conversation": name, "expected": spec["expected"],
                     "routed_to": result.last_agent.name})
    return rows


if __name__ == "__main__":
    for row in run_demo():
        print(row)
