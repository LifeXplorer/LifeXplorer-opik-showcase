"""The programmatic check shared by compiling and local evaluation."""

import re

CARD_TAG = re.compile(r"\|\s*card:\s*([A-Z]+-\d+)\s*$")


def house_format_metric(example, prediction, trace=None) -> bool:
    """Pass if the answer ends in one '| card: <ID>' tag naming the right card
    and mentions the key fact. No LLM judge, so compiling spends no judge tokens."""
    answer = prediction.answer.strip()
    match = CARD_TAG.search(answer)
    if not match or match.group(1) != example.card:
        return False
    return example.key_fact.lower() in answer.lower()
