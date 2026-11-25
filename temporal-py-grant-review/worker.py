"""The worker process: runs the workflow code and the activities (including the OpenAI calls)."""
import asyncio
import os
import signal

from temporalio.client import Client
from temporalio.worker import Worker

from activities import check_budget, draft_letter, screen_application
from models import TASK_QUEUE
from otel import setup_tracing, tracing_interceptor
from workflows import GrantReview


async def main() -> None:
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    provider = setup_tracing("grant-worker")  # this process exports the workflow, activity and LLM spans
    # The interceptor on the client is inherited by the worker, so workflow and activity spans
    # continue the trace context the client started.
    client = await Client.connect(address, interceptors=[tracing_interceptor()])
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[GrantReview],
        activities=[screen_application, check_budget, draft_letter],
    )
    stop = asyncio.Event()
    asyncio.get_running_loop().add_signal_handler(signal.SIGINT, stop.set)
    try:
        async with worker:
            print(f"WORKER_READY on {address}, task queue {TASK_QUEUE!r}", flush=True)
            await stop.wait()
    finally:
        provider.shutdown()  # flushes the batched spans to Opik before this process exits


if __name__ == "__main__":
    asyncio.run(main())
