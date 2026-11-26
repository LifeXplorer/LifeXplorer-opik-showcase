"""Regenerate flows/makerspace-assistant.json: Langflow's own 'Basic Prompting' starter,
re-pointed at the makerspace guide in docs/ and at gpt-4o-mini. Only needed if you edit the guide;
the generated JSON is committed so the demo imports it as-is."""
import copy
import json
from pathlib import Path

import langflow

HERE = Path(__file__).parent
STARTER = Path(langflow.__file__).parent / "initial_setup/starter_projects/Basic Prompting.json"

PERSONA = (
    "You are Sprocket, the front-desk assistant at Quillmere Makerspace. Answer member questions "
    "about tool booking, badges, safety rules and opening hours using ONLY the guide below. "
    "Be brief (max 4 sentences). If the guide does not cover something, say so and point to the front desk.\n\n"
    "=== MEMBER GUIDE ===\n"
)


def main() -> None:
    flow = json.loads(STARTER.read_text())
    guide = (HERE / "docs/makerspace-guide.md").read_text()
    # Prompt templates treat {braces} as variables, so double any literal ones in the guide.
    template = PERSONA + guide.replace("{", "{{").replace("}", "}}")

    flow["name"] = "Makerspace Assistant"
    flow["description"] = "Chat assistant for Quillmere Makerspace: tool booking, badges, safety, hours."
    flow["endpoint_name"] = "makerspace"
    flow["tags"] = []
    flow["data"]["nodes"] = [n for n in flow["data"]["nodes"] if n["type"] == "genericNode"]
    for node in flow["data"]["nodes"]:
        t = node["data"]["node"]["template"]
        kind = node["data"]["type"]
        if kind == "Prompt":
            t["template"]["value"] = template
        elif kind == "LanguageModelComponent":
            opts = copy.deepcopy(t["model"]["options"])
            openai = next(o for o in opts if o["provider"] == "OpenAI")
            openai["name"] = "gpt-4o-mini"
            openai["metadata"]["reasoning_models"] = []
            t["model"]["value"] = [openai]
            t["temperature"]["value"] = 0.1
            # Read the key from the OPENAI_API_KEY Langflow global variable (fed from the environment).
            t["api_key"]["value"] = "OPENAI_API_KEY"
            t["api_key"]["load_from_db"] = True
            for k in ("_frontend_node_flow_id", "_frontend_node_folder_id"):
                t.pop(k, None)
    flow.pop("id", None)
    flow.pop("last_tested_version", None)
    out = HERE / "flows/makerspace-assistant.json"
    out.write_text(json.dumps(flow, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
