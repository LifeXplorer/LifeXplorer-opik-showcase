"""Illustrate two pages with each of two brief versions and trace it all in Opik."""

from __future__ import annotations

import difflib
import os
import sys
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Walk up to the nearest .env for provider keys; real env vars win.
load_dotenv(find_dotenv(usecwd=True))
os.environ.pop("OPENAI_BASE_URL", None)

import opik  # noqa: E402

from illustrator import illustrate_page, make_clients  # noqa: E402
from storybook import (  # noqa: E402
    BRIEF_V1, BRIEF_V2, PAGES, PROJECT, PROMPT_NAME, V1_CHANGE, V2_CHANGE,
)


def register_briefs(client: opik.Opik):
    """Put both brief versions in the Opik prompt library (once) and read them back."""
    # create_prompt only makes a new version when the text differs from the
    # latest one, so re-registering v1 after v2 would add a bogus v3. Register
    # only when the prompt is new; afterwards the library is the source of truth.
    if client.get_prompt(PROMPT_NAME, project_name=PROJECT) is None:
        client.create_prompt(PROMPT_NAME, BRIEF_V1, change_description=V1_CHANGE,
                             tags=["storybook"], project_name=PROJECT)
        client.create_prompt(PROMPT_NAME, BRIEF_V2, change_description=V2_CHANGE,
                             tags=["storybook"], project_name=PROJECT)
        print(f'Registered "{PROMPT_NAME}" (v1 + v2) in the prompt library.')
    v1 = client.get_prompt(PROMPT_NAME, version="v1", project_name=PROJECT, no_cache=True)
    v2 = client.get_prompt(PROMPT_NAME, project_name=PROJECT, no_cache=True)
    if v1 is None or v2 is None:
        raise RuntimeError("brief versions missing from the prompt library")
    return v1, v2


def show_diff(v1, v2) -> None:
    print(f"\nWhat {v2.version} changed in the brief:")
    for line in difflib.unified_diff(v1.prompt.splitlines(), v2.prompt.splitlines(),
                                     v1.version, v2.version, lineterm="", n=0):
        print("  " + line)


def main() -> int:
    if not os.environ.get("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not set. Add it to .env and re-run.", file=sys.stderr)
        return 1
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT)
    opik_client = opik.Opik(project_name=PROJECT)
    openai_client = make_clients()
    out_dir = Path("output")

    v1, v2 = register_briefs(opik_client)
    show_diff(v1, v2)

    for brief in (v1, v2):
        print(f"\nIllustrating with brief {brief.version}:")
        for page in PAGES:
            r = illustrate_page(openai_client, brief, page, out_dir)
            print(f"  {page['id']}: {r['file']} ({r['bytes'] // 1024} KiB)\n    scene: {r['scene']}")

    # flush_tracker sends queued traces/spans/attachments before the process exits;
    # without it the last pictures may never reach Opik.
    opik.flush_tracker()
    opik_client.flush()
    print(f'\nDone. Open project "{PROJECT}" in Opik: 4 traces, each with its PNG attached.')
    return 0


if __name__ == "__main__":
    sys.exit(main())
