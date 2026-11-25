"""Opik wiring for LiteLLM: one callback, one flush."""

import logging
import os
import warnings

import litellm
import opik

from review_router.config import PROJECT_NAME


def setup_tracing() -> None:
    """Attach LiteLLM's OpikLogger so every completion is logged as an llm span."""
    # The callback reads the project name when it is created, so set it first.
    # Without it traces land in "Default Project" instead of this example's project.
    os.environ.setdefault("OPIK_PROJECT_NAME", PROJECT_NAME)
    from litellm.integrations.opik.opik import OpikLogger

    # Outside an event loop OpikLogger logs a scary but harmless "no running event loop" traceback
    # while it falls back to synchronous sending; mute it for the constructor only.
    litellm_log = logging.getLogger("LiteLLM")
    previous = litellm_log.level
    litellm_log.setLevel(logging.CRITICAL)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*periodic_flush.*", category=RuntimeWarning)
        # OpikLogger turns each completion into a span of type llm, with model, token usage and cost filled in.
        litellm.callbacks = [OpikLogger()]
    litellm_log.setLevel(previous)


def flush() -> None:
    # The CLI exits right after the last call; flushing makes sure queued traces and spans are sent first.
    opik.flush_tracker()
