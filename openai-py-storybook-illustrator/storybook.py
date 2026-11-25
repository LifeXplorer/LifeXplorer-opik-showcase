"""The fictional book and the two versions of the illustration brief."""

PROJECT = "openai-py-storybook-illustrator"
PROMPT_NAME = "storybook-illustration-brief"

# Mustache template: v1 is what a first-time author writes. Use plain {{var}}:
# in opik 2.3.4 it does not HTML-escape, and {{{var}}} would keep literal braces.
BRIEF_V1 = """Illustration for a children's picture book.
Character: {{character}}
Scene: {{scene}}
Mood: warm and magical."""

# v2 adds the rules a picture-book editor would have asked for after seeing v1.
BRIEF_V2 = """Illustration for a children's picture book.
Character: {{character}}
Scene: {{scene}}
Mood: warm and magical.

Style rules:
- Soft watercolor with visible paper grain, dusk palette of indigo, amber and moss green.
- Keep the character exactly as described on every page: same coat, same lantern, same hair.
- No lettering, captions, signs or speech bubbles anywhere in the picture.
- Wide landscape composition with calm space in the upper third for the page text."""

V1_CHANGE = "Initial brief: character, scene, mood"
V2_CHANGE = "Add watercolor palette, character consistency, no-lettering and text-space rules"

CHARACTER = (
    "Wren, a seven-year-old girl with a black bob, a mustard raincoat with big "
    "patches, and a patchwork paper lantern on a stick"
)

# Fictional book: "Wren and the Lantern Moths".
PAGES = [
    {
        "id": "page-1",
        "text": "Wren climbed the hill at dusk, her patchwork lantern swinging, "
        "to find out where the lantern moths go at night.",
    },
    {
        "id": "page-2",
        "text": "At the very top, a thousand moths lifted out of the fireweed and "
        "drew a glowing staircase up into the sky.",
    },
]
