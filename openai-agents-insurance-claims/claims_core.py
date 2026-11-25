"""Plain claims logic: policy lookup, payout estimate, claim intake.

No agent or tracing code lives here, so it can be unit-tested offline.
"""

import json
import uuid
from pathlib import Path

POLICIES = json.loads(
    (Path(__file__).parent / "data" / "policies.json").read_text()
)


def find_policy(policy_id: str) -> dict | None:
    for policy in POLICIES:
        if policy["policy_id"].upper() == policy_id.strip().upper():
            return policy
    return None


def lookup_policy(policy_id: str) -> dict:
    policy = find_policy(policy_id)
    return policy if policy else {"error": f"policy {policy_id} not found"}


def estimate_payout(policy_id: str, damage_usd: float) -> dict:
    """Payout = damage minus deductible, capped at the coverage limit."""
    policy = find_policy(policy_id)
    if policy is None:
        return {"error": f"policy {policy_id} not found"}
    if not policy["active"]:
        return {"error": f"policy {policy_id} is lapsed, claim not payable"}
    payout = min(max(damage_usd - policy["deductible_usd"], 0),
                 policy["coverage_limit_usd"])
    return {"policy_id": policy["policy_id"], "damage_usd": damage_usd,
            "deductible_usd": policy["deductible_usd"],
            "estimated_payout_usd": payout}


def open_claim(policy_id: str, summary: str) -> dict:
    policy = find_policy(policy_id)
    if policy is None:
        return {"error": f"policy {policy_id} not found"}
    if not policy["active"]:
        return {"error": f"policy {policy_id} is lapsed, cannot open claim"}
    return {"status": "opened", "claim_id": f"CLM-{uuid.uuid4().hex[:6].upper()}",
            "policy_id": policy["policy_id"], "summary": summary}
