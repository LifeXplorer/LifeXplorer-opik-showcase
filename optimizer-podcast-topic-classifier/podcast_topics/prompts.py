"""The starting prompt: a first draft that names topics loosely and never says how to answer."""

MODEL = "gpt-4o-mini"

BASELINE_SYSTEM = """\
You are a friendly assistant for Nightlight Audio, a podcast network. Read the
episode blurb and say which kind of show it belongs to: science, history,
business, true crime or culture."""

# {episode} is filled with the blurb being classified.
USER_TEMPLATE = "{episode}"


def to_library_messages(messages: list[dict]) -> list[dict]:
    """Convert optimizer messages ({episode}) to prompt-library messages ({{episode}}).

    The optimizer formats variables with single braces; Opik's prompt library
    uses mustache double braces, so the winner must be translated before saving.
    """
    return [{**m, "content": m["content"].replace("{episode}", "{{episode}}")} for m in messages]
