"""Opik wiring: one callback traces every DSPy call."""

import os

PROJECT_NAME = "dspy-chess-openings-qa"


def install_opik_callback() -> None:
    """Attach OpikCallback to DSPy.

    Each program call becomes a trace; the ChainOfThought, Predict and LM
    calls inside it become nested spans (the LM span is type llm, with token
    usage and cost). log_graph=True also stores a mermaid diagram of the module
    graph in the trace metadata. Without this callback nothing reaches Opik.
    """
    # Set before the first Opik client is created so every trace lands in this project.
    os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

    import dspy
    from opik.integrations.dspy.callback import OpikCallback

    dspy.configure(callbacks=[OpikCallback(project_name=PROJECT_NAME, log_graph=True)])
