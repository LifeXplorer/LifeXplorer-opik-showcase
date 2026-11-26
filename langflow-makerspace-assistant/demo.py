"""Headless demo: start Langflow, import the flow over its API, ask three member questions, stop Langflow.

No Opik code lives here. Langflow's built-in Opik tracer switches on by itself when
OPIK_URL_OVERRIDE (or OPIK_API_KEY) is in the server's environment, so this script only sets env vars.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

HERE = Path(__file__).parent
PROJECT = "langflow-makerspace-assistant"
PORT = int(os.getenv("LANGFLOW_PORT", "7870"))
BASE = f"http://127.0.0.1:{PORT}"
QUESTIONS = [
    "I want to book a 3D printer for Saturday afternoon. What do I need first, and what does it cost?",
    "Can I cut a sheet of vinyl on the laser cutter if I'm wearing closed-toe shoes?",
    "Are you open on Sundays?",
]


def call(method: str, path: str, body: dict | None = None, token: str | None = None, api_key: str | None = None) -> dict:
    req = urllib.request.Request(
        BASE + path,
        method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={
            "Content-Type": "application/json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
            **({"x-api-key": api_key} if api_key else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"{method} {path} -> {e.code}: {e.read().decode()[:500]}")


def answer_text(run: dict) -> str:
    # Walk the run result down to the Chat Output message text.
    return run["outputs"][0]["outputs"][0]["results"]["message"]["text"]


def main() -> None:
    load_dotenv(find_dotenv())  # walks up to the repo-root .env for OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("OPENAI_API_KEY is not set (put it in .env)")
    workdir = Path(tempfile.mkdtemp(prefix="makerspace-langflow-"))
    env = {
        **os.environ,
        # Langflow's native Opik tracer reads these three. Without OPIK_URL_OVERRIDE (or an API key)
        # it stays silent: no error, just no traces.
        "OPIK_URL_OVERRIDE": os.getenv("OPIK_URL_OVERRIDE", "http://localhost:5173/api/"),
        "OPIK_WORKSPACE": os.getenv("OPIK_WORKSPACE", "default"),
        # Langflow 1.8 takes the Opik project from LANGCHAIN_PROJECT, not OPIK_PROJECT_NAME;
        # leave it unset and every trace lands in a project called "Langflow".
        "LANGCHAIN_PROJECT": PROJECT,
        "LANGFLOW_AUTO_LOGIN": "true",
        "LANGFLOW_CONFIG_DIR": str(workdir),
        "LANGFLOW_DATABASE_URL": f"sqlite:///{workdir}/langflow.db",
        "LANGFLOW_VARIABLES_TO_GET_FROM_ENVIRONMENT": "OPENAI_API_KEY",
        "LANGFLOW_DO_NOT_TRACK": "true",
        "DO_NOT_TRACK": "true",
    }
    server = subprocess.Popen(
        [sys.executable, "-m", "langflow", "run", "--host", "127.0.0.1", "--port", str(PORT), "--backend-only"],
        cwd=HERE, env=env, stdout=open(workdir / "server.log", "w"), stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(180):
            try:
                urllib.request.urlopen(BASE + "/health", timeout=2)
                break
            except Exception:
                if server.poll() is not None:
                    sys.exit(f"Langflow exited early, see {workdir}/server.log")
                time.sleep(2)
        else:
            sys.exit("Langflow did not become healthy in time")
        print(f"Langflow up on {BASE}")

        token = call("GET", "/api/v1/auto_login")["access_token"]
        # Since Langflow 1.5 the run endpoint needs an API key even with auto-login, so mint one.
        api_key = call("POST", "/api/v1/api_key/", {"name": "demo"}, token)["api_key"]
        flow = json.loads((HERE / "flows/makerspace-assistant.json").read_text())
        created = call("POST", "/api/v1/flows/", flow, token)
        print(f"Imported flow '{created['name']}' ({created['id']})")

        # One session id for all three turns: Langflow forwards it to Opik as the thread id.
        session = f"member-{uuid.uuid4().hex[:8]}"
        for q in QUESTIONS:
            run = call("POST", f"/api/v1/run/{created['id']}?stream=false",
                       {"input_value": q, "input_type": "chat", "output_type": "chat", "session_id": session}, api_key=api_key)
            print(f"\nQ: {q}\nA: {answer_text(run)}")
    finally:
        server.terminate()
        try:
            server.wait(timeout=30)  # a clean stop gives the tracer time to flush
        except subprocess.TimeoutExpired:
            server.kill()
    print(f"\nDone. Open Opik project '{PROJECT}' (server log: {workdir}/server.log)")


if __name__ == "__main__":
    main()
