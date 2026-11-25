"""Self-contained demo: starts a local Temporal dev server, spawns the worker as a separate
OS process, acts as the client for each application in data/applications.json, then cleans up."""
import asyncio
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

from models import TASK_QUEUE, Application, ReviewResult
from workflows import GrantReview

HERE = Path(__file__).parent
PORT, UI_PORT = 7290, 8290


def load_applications() -> list[Application]:
    return [Application(**row) for row in json.loads((HERE / "data" / "applications.json").read_text())]


async def start_worker(address: str) -> subprocess.Popen:
    proc = subprocess.Popen(
        [sys.executable, str(HERE / "worker.py")],
        env={**os.environ, "TEMPORAL_ADDRESS": address},
        stdout=subprocess.PIPE,
        text=True,
    )
    loop = asyncio.get_running_loop()
    while True:
        line = await loop.run_in_executor(None, proc.stdout.readline)
        if not line:
            raise RuntimeError(f"worker exited early with code {proc.poll()}")
        print(f"[worker] {line}", end="")
        if "WORKER_READY" in line:
            return proc


async def review(client: Client, application: Application) -> ReviewResult:
    handle = await client.start_workflow(
        GrantReview.run, application, id=application.application_id, task_queue=TASK_QUEUE
    )
    return await handle.result()


async def main() -> None:
    print("Starting local Temporal dev server (downloads on first run)...")
    async with await WorkflowEnvironment.start_local(port=PORT, ui_port=UI_PORT) as env:
        address = f"127.0.0.1:{PORT}"
        worker = await start_worker(address)
        client = await Client.connect(address)
        try:
            for application in load_applications():
                print(f"\n=== {application.application_id}: {application.applicant}")
                result = await review(client, application)
                print(f"Category: {result.screening.category} (fit {result.screening.fit_score}/5)")
                print(f"Requested ${result.budget.requested_amount}, fund has ${result.budget.remaining_before}")
                print(f"Decision: {result.decision}\n{result.letter}")
        finally:
            print("\nShutting down...")
            worker.send_signal(signal.SIGINT)
            worker.wait(timeout=30)


if __name__ == "__main__":
    asyncio.run(main())
