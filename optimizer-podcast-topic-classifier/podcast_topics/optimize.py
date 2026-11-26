"""Hand the baseline prompt to the Opik Agent Optimizer and save the winner."""

import opik
from opik_optimizer import ChatPrompt, MetaPromptOptimizer

from .classifier import PROJECT_NAME
from .episodes import EPISODES
from .metric import topic_accuracy
from .prompts import BASELINE_SYSTEM, USER_TEMPLATE, to_library_messages

OPTIMIZER_MODEL = "openai/gpt-4o-mini"  # LiteLLM naming: classifies and reasons about failures
DATASET_NAME = "optimizer-podcast-topic-classifier-episodes"
LIBRARY_PROMPT_NAME = "podcast-topic-classifier"
MAX_TRIALS = 4  # candidate prompts the optimizer may score: the budget cap


def run() -> None:
    client = opik.Opik(project_name=PROJECT_NAME)

    # The dataset is what the optimizer climbs against; Opik dedupes identical
    # rows, so re-runs reuse it. It appears under Datasets and names the run.
    dataset = client.get_or_create_dataset(
        name=DATASET_NAME,
        description=f"{len(EPISODES)} labeled Nightlight Audio episode blurbs (5 topics)",
    )
    dataset.insert([{"episode": blurb, "label": label} for blurb, label in EPISODES])

    prompt = ChatPrompt(
        name=LIBRARY_PROMPT_NAME,
        system=BASELINE_SYSTEM,
        user=USER_TEMPLATE,  # {episode} is filled from the dataset column
        model=OPTIMIZER_MODEL,
    )

    # Version 1 in the prompt library is the baseline, saved before optimizing so
    # the library ends up telling the whole story: v1 mediocre, v2 optimized.
    client.create_chat_prompt(
        name=LIBRARY_PROMPT_NAME,
        messages=to_library_messages(
            [
                {"role": "system", "content": BASELINE_SYSTEM},
                {"role": "user", "content": USER_TEMPLATE},
            ]
        ),
        change_description="Baseline hand-written prompt (pre-optimization)",
        project_name=PROJECT_NAME,
    )

    # Creates an optimization run: each trial is an experiment scored on every
    # episode, and the run page plots the score curve across trials.
    optimizer = MetaPromptOptimizer(model=OPTIMIZER_MODEL, prompts_per_round=3, seed=42, verbose=1)
    result = optimizer.optimize_prompt(
        prompt=prompt,
        dataset=dataset,
        metric=topic_accuracy,
        n_samples=len(EPISODES),
        max_trials=MAX_TRIALS,
        project_name=PROJECT_NAME,  # trial evaluations and reasoning calls become traces here
    )

    initial = result.initial_score if result.initial_score is not None else 0.0
    best = result.score
    cost = result.llm_cost_total
    print("\n" + "=" * 64)
    print(f"baseline accuracy : {initial:.3f}")
    print(f"best accuracy     : {best:.3f}  ({best - initial:+.3f})")
    print(f"trials completed  : {result.details.get('trials_completed')}  (budget: {MAX_TRIALS})")
    print(f"total llm cost    : {'$%.4f' % cost if cost is not None else 'unavailable'}")

    # get_run_link() opens in whatever project the UI last showed, so the run can look
    # empty; build a project-pinned link from the optimization's own project id.
    info = client.rest_client.optimizations.get_optimization_by_id(result.optimization_id)
    ui_base = client.config.url_override.rstrip("/").removesuffix("/api")
    print(
        f"optimization run  : {ui_base}/{client.config.workspace}/projects/"
        f"{info.project_id}/optimizations/{result.optimization_id}"
    )
    print("=" * 64)

    # Only a real gain earns version 2; the library keeps v1 otherwise.
    if best > initial:
        client.create_chat_prompt(
            name=LIBRARY_PROMPT_NAME,
            messages=to_library_messages(result.prompt.get_messages()),
            change_description=f"MetaPromptOptimizer winner: accuracy {initial:.3f} -> {best:.3f} on {DATASET_NAME}",
            project_name=PROJECT_NAME,
        )
        print(f"\nSaved the winner as '{LIBRARY_PROMPT_NAME}' v2 in the prompt library.\n")
        print(result.prompt.get_messages()[0]["content"])
    else:
        print("\nNo improvement over the baseline; the library keeps only v1.")
    opik.flush_tracker()
