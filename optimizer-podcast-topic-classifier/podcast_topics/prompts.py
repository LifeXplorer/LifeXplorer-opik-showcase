"""The starting prompt: a first draft that names topics loosely and never says how to answer."""

MODEL = "gpt-4o-mini"

BASELINE_SYSTEM = """\
You help organize episodes for Nightlight Audio, a podcast network. Look at the
episode blurb and work out whether it is about science, history, business,
true crime, or culture, and answer with the topic."""

# {episode} is filled with the blurb being classified.
USER_TEMPLATE = "{episode}"
