"""The worker process: runs the workflow code and the activities (including the OpenAI calls)."""
import asyncio
import os

from temporalio.client import Client
from temporalio.worker import Worker

from activities import check_budget, draft_letter, screen_application
from models import TASK_QUEUE
from workflows import GrantReview


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    client = await Client.connect(address)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GrantReview],
        activities=[screen_application, check_budget, draft_letter],
    )
    print(f"WORKER_READY on {address}, task queue {TASK_QUEUE!r}", flush=True)
    await worker.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
