"""Deterministic check that a RecipeCard only contains what the note says.

This is the cheap, offline counterpart of the LLM-judge assertions: every
number on the card (servings, minutes, temperature, quantities) and every
ingredient name must be traceable to the source text.
"""

import re
from fractions import Fraction

NUMBER_WORDS = {
    "half": "0.5", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10", "twelve": "12",
}
FILLER = {"a", "an", "the", "of", "fresh", "ripe", "very", "large", "small", "medium", "to", "taste"}


def _numbers_in(text: str) -> set[str]:
    """All numbers in the text, normalised: '1 1/2' -> 1.5, '1/2' -> 0.5, 'half' -> 0.5."""
    text = text.lower()
    found: set[str] = set()
    for whole, frac in re.findall(r"(?:(\d+)\s+)?(\d+/\d+)", text):
        value = float(Fraction(frac)) + (int(whole) if whole else 0)
        found.add(f"{value:g}")
    for num in re.findall(r"\d+(?:\.\d+)?", text):
        found.add(f"{float(num):g}")
    for word, value in NUMBER_WORDS.items():
        if re.search(rf"\b{word}\b", text):
            found.add(f"{float(value):g}")
    return found


def _words(text: str) -> set[str]:
    return set(re.findall(r"[a-z]+", text.lower()))


def _stem(word: str) -> str:
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _in_source(word: str, source_words: set[str]) -> bool:
    # 'bicarb' in the note still grounds 'bicarbonate'; prefixes need 5+ letters.
    return word in source_words or any(
        len(s) >= 5 and (word.startswith(s) or s.startswith(word)) for s in source_words
    )


def find_ungrounded(card: dict, source: str) -> list[str]:
    """Return a description of every value on the card that the note never supports."""
    source_numbers = _numbers_in(source)
    source_words = {_stem(w) for w in _words(source)}
    problems: list[str] = []

    for field in ("servings", "prep_minutes", "cook_minutes", "oven_temp_c"):
        value = card.get(field)
        if value is not None and f"{float(value):g}" not in source_numbers:
            # 350F in the note may legitimately be stored as ~175C; allow Fahrenheit.
            if field == "oven_temp_c" and any(
                abs((float(n) - 32) * 5 / 9 - float(value)) < 6 for n in source_numbers
            ):
                continue
            problems.append(f"{field}={value} is not in the note")

    for ing in card.get("ingredients", []):
        name_words = [_stem(w) for w in _words(ing["name"]) if w not in FILLER]
        if name_words and not any(_in_source(w, source_words) for w in name_words):
            problems.append(f"ingredient '{ing['name']}' is not in the note")
        qty = ing.get("quantity")
        if qty:
            for num in _numbers_in(str(qty)):
                if num not in source_numbers:
                    problems.append(f"quantity '{qty}' of {ing['name']} is not in the note")
                    break
    return problems
