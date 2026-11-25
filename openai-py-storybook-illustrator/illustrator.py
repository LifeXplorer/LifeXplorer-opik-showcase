"""Page text -> scene sentence -> brief -> picture, traced into Opik."""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Any

import opik
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai

from storybook import CHARACTER, PROJECT, PROMPT_NAME

# Not every API key can use gpt-image-1 (BadRequest: "model does not exist");
# gpt-image-1-mini is the cheap default, override with IMAGE_MODEL.
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1-mini")
IMAGE_SIZE = "1024x1024"
IMAGE_QUALITY = "low"  # cheapest tier, about a cent per picture
SCENE_MODEL = "gpt-4o-mini"


def make_clients(api_key: str | None = None) -> Any:
    """Return an OpenAI client whose chat calls are traced."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    # track_openai wraps the client: every chat completion becomes an llm span
    # with token usage and cost, nested under the active trace.
    return track_openai(client, project_name=PROJECT)


def render_brief(brief: Any, scene: str) -> str:
    """Fill the library template (mustache) with the character and scene."""
    return brief.format(character=CHARACTER, scene=scene)


def describe_scene(client: Any, page_text: str) -> str:
    """Turn the page's prose into one concrete, paintable sentence."""
    response = client.chat.completions.create(
        model=SCENE_MODEL,
        temperature=0.3,
        max_tokens=80,
        messages=[
            {
                "role": "system",
                "content": "You are a picture-book art director. Reply with ONE "
                "sentence describing only what is visible in the illustration: "
                "setting, light, and the character's pose. No dialogue, no text.",
            },
            {"role": "user", "content": page_text},
        ],
    )
    return (response.choices[0].message.content or "").strip()


# type="llm" makes this an llm span, so model, provider and usage are shown and
# cost can be computed. images.generate is not auto-tracked by track_openai,
# so we log the span ourselves.
@opik.track(name="images.generate", type="llm", project_name=PROJECT)
def generate_image(client: Any, image_prompt: str, out_path: Path) -> dict[str, Any]:
    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=image_prompt,
        size=IMAGE_SIZE,
        quality=IMAGE_QUALITY,
        n=1,
    )
    png = base64.b64decode(result.data[0].b64_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(png)

    usage = getattr(result, "usage", None)
    # Attachments are uploaded next to the span: the Opik UI renders the PNG
    # inline, so you see the picture beside the prompt that produced it.
    # Usage/model/provider on the span give token counts and an estimated cost.
    opik_context.update_current_span(
        model=IMAGE_MODEL,
        provider="openai",
        usage={
            "prompt_tokens": getattr(usage, "input_tokens", 0),
            "completion_tokens": getattr(usage, "output_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }
        if usage
        else None,
        metadata={"size": IMAGE_SIZE, "quality": IMAGE_QUALITY},
        attachments=[Attachment(data=str(out_path), file_name=out_path.name, content_type="image/png")],
    )
    return {"file": str(out_path), "bytes": len(png)}


# The entry point: one trace per illustrated page, with the describe-scene llm
# span and the images.generate llm span nested beneath it.
@opik.track(name="illustrate-page", project_name=PROJECT)
def illustrate_page(
    client: Any, brief: Any, page: dict[str, str], out_dir: Path
) -> dict[str, Any]:
    scene = describe_scene(client, page["text"])
    image_prompt = render_brief(brief, scene)
    out_path = out_dir / f"{brief.version}-{page['id']}.png"
    image = generate_image(client, image_prompt, out_path)

    # prompts= links the exact library version to this trace (shows up in the
    # trace's prompt section); the tags/metadata make traces filterable by version.
    opik_context.update_current_trace(
        prompts=[brief],
        tags=[brief.version, page["id"]],
        metadata={
            "prompt_name": PROMPT_NAME,
            "prompt_version": brief.version,
            "page": page["id"],
        },
        attachments=[Attachment(data=str(out_path), file_name=out_path.name, content_type="image/png")],
    )
    return {"scene": scene, "image_prompt": image_prompt, **image}
