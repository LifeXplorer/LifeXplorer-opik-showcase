"""Load the fictional sample diffs from data/diffs."""

from dataclasses import dataclass
from pathlib import Path

from review_router.config import DIFFS_DIR


@dataclass(frozen=True)
class Diff:
    name: str  # file stem, e.g. "03-sql-search"
    text: str


def load_diffs(directory: Path = DIFFS_DIR, only: list[str] | None = None) -> list[Diff]:
    """Read every *.diff in `directory`, optionally keeping names that contain one of `only`."""
    diffs = [Diff(p.stem, p.read_text()) for p in sorted(directory.glob("*.diff"))]
    if only:
        diffs = [d for d in diffs if any(token in d.name for token in only)]
    return diffs
