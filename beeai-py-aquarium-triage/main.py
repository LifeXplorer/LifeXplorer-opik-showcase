"""Run three scripted aquarium alerts through the triage agent. `uv run main.py`."""
import asyncio
import os
import sys

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))  # picks up the repo-root .env (provider keys only)

PROJECT = "beeai-py-aquarium-triage"
ALERTS = [
    # Reef ammonia should be zero, so even a small reading is past the urgent line.
    {"tank_id": "reef-01", "parameter": "ammonia_ppm", "reading": 0.25,
     "note": "Probe test after the new cleaner shrimp went in yesterday."},
    # Slightly high pH for shrimp: outside the safe band but short of urgent.
    {"tank_id": "shrimp-04", "parameter": "ph", "reading": 7.6,
     "note": "Routine morning reading; shrimp are active and feeding."},
    # Warm but legal for a community tank: should come back ok.
    {"tank_id": "comm-07", "parameter": "temperature_c", "reading": 26.5,
     "note": "Room was warm overnight; fish look normal."},
]


async def run() -> None:
    from triage import triage_alert

    for i, alert in enumerate(ALERTS, 1):
        print(f"\n=== Alert {i}: {alert['tank_id']} {alert['parameter']}={alert['reading']} ===")
        result = await triage_alert(alert)
        for k, v in result.items():
            print(f"{k:>8}: {v}")


def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        sys.exit("Missing OPENAI_API_KEY (put it in .env, see .env.example).")
    # Tracing must be switched on before the first agent runs so BeeAI's spans are captured.
    from tracing import setup_tracing

    shutdown = setup_tracing(PROJECT)
    try:
        asyncio.run(run())
    finally:
        shutdown()  # flush: batched spans are lost on exit without this
    print(f'\nDone. Open the "{PROJECT}" project in Opik.')


if __name__ == "__main__":
    main()
