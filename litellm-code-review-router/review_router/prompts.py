"""The review prompt, identical for every model so the comparison is fair."""

SYSTEM_PROMPT = (
    "You are a code reviewer. Summarize the pull request diff for the reviewer in this format:\n"
    "SUMMARY: one sentence on what changed.\n"
    "RISKS: up to three bullets, or 'none'.\n"
    "VERDICT: approve, request-changes, or comment."
)


def build_messages(diff_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Review this diff:\n\n{diff_text}"},
    ]
