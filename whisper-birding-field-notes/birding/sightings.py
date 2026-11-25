"""Pure logic for the sighting log: no network, no Opik. Unit-tested offline."""

import json
from pathlib import Path

CHECKLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "checklist.json"


def load_checklist(path: Path = CHECKLIST_PATH) -> set[str]:
    return set(json.loads(path.read_text()))


def normalize_species(name: str) -> str:
    """'eurasian  jay' -> 'Eurasian Jay'; 'long-tailed tit' -> 'Long-tailed Tit'."""
    def fix(word: str) -> str:
        return word[:1].upper() + word[1:].lower()
    return " ".join(fix(w) for w in name.split())


def clean_sightings(raw: list[dict], checklist: set[str]) -> list[dict]:
    """Merge duplicate species, drop rows without a positive integer count,
    and flag species that are not on the site checklist (likely mishearings)."""
    merged: dict[str, dict] = {}
    for row in raw:
        species = normalize_species(str(row.get("species", "")))
        count = row.get("count")
        if not species or isinstance(count, bool) or not isinstance(count, int) or count < 1:
            continue
        entry = merged.setdefault(species, {"species": species, "count": 0, "notes": []})
        entry["count"] += count
        if row.get("note"):
            entry["notes"].append(str(row["note"]))
    return [
        {
            "species": e["species"],
            "count": e["count"],
            "note": "; ".join(e["notes"]),
            "on_checklist": e["species"] in checklist,
        }
        for e in sorted(merged.values(), key=lambda e: e["species"])
    ]


def render_log(title: str, observer: str, sightings: list[dict]) -> str:
    """Markdown sighting log, with a warning marker on off-checklist species."""
    lines = [f"## {title} (observer: {observer})", "", "| Species | Count | Note |", "|---|---|---|"]
    for s in sightings:
        flag = "" if s["on_checklist"] else " (not on checklist)"
        lines.append(f"| {s['species']}{flag} | {s['count']} | {s['note']} |")
    total = sum(s["count"] for s in sightings)
    lines += ["", f"{len(sightings)} species, {total} individuals."]
    return "\n".join(lines)
