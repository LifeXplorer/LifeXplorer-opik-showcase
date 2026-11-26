"""Compile the program with BootstrapFewShot."""

import dspy

from .examples import trainset
from .metric import house_format_metric


def compile_program(program: dspy.Module) -> dspy.Module:
    """A teacher run over the training tickets keeps the attempts that pass the
    metric (reasoning included) and bakes up to four into the prompt as demos."""
    optimizer = dspy.BootstrapFewShot(
        metric=house_format_metric,
        max_bootstrapped_demos=4,
        max_labeled_demos=4,
        max_rounds=1,
    )
    return optimizer.compile(program, trainset=trainset)
