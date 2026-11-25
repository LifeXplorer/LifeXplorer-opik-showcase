"""Dataset and experiment helpers: score the graph with Hallucination and ContextPrecision."""

import opik
from opik.evaluation import evaluate
from opik.evaluation.metrics import ContextPrecision, Hallucination

DATASET_NAME = "stargazing-handbook-questions"

# Each item has the question and a reference answer. The "multi-section" items need facts
# from two different handbook sections, which is where a too-small k starts to fail.
DATASET_ITEMS = [
    {"question": "How long does the 130 mm Dobsonian need to cool down?",
     "expected_output": "30 minutes."},
    {"question": "What is the Bortle rating of Marrow Ridge?",
     "expected_output": "Marrow Ridge is a Bortle 3 site."},
    {"question": "How many minutes should I allow for dark adaptation?",
     "expected_output": "25 minutes, using only dim red light."},
    {"question": "Which star party is open to non-members?",
     "expected_output": "The Perseid Picnic in August, with guests accompanied by a member."},
    {"question": "What exposure and ISO does the club recommend for a fixed-tripod Milky Way shot?",
     "expected_output": "A 20-second exposure at ISO 3200 with the lens fully open."},
    {"question": "What would a family membership plus the loaner telescope deposit cost me in total?",
     "expected_output": "70 pounds for the family membership plus a refundable 25 pound deposit, 95 pounds up front."},
    {"question": "Which observing site should I use for a Milky Way session, and what do I need to get in?",
     "expected_output": "Marrow Ridge (Bortle 3); members get the quarterly gate code by email."},
    {"question": "Can I buy a telescope through the club?",
     "expected_output": "The handbook doesn't say."},
]


def get_dataset(client: opik.Opik) -> opik.Dataset:
    # A named dataset makes every experiment run over the same questions, so runs compare
    # row by row in the Opik UI. insert() deduplicates, so re-running does not add rows.
    dataset = client.get_or_create_dataset(name=DATASET_NAME)
    dataset.insert(DATASET_ITEMS)
    return dataset


def run_experiment(dataset: opik.Dataset, traced_app, experiment_name: str, k: int):
    def task(item: dict) -> dict:
        # Invoking the traced graph logs one trace per dataset item, linked to the experiment
        # item. "context" is returned so the judge metrics can read the retrieved sections.
        result = traced_app.invoke({"question": item["question"]})
        return {"output": result["answer"], "context": result["context"]}

    # evaluate() creates the experiment, runs task() per item and attaches each metric as a
    # feedback score. track=False keeps the judge's own calls out of the project's traces.
    # The metric inputs are named input/output/context, so the dataset field `question` is
    # mapped onto `input`.
    return evaluate(
        dataset=dataset,
        task=task,
        scoring_metrics=[
            Hallucination(model="gpt-4o-mini", track=False),
            ContextPrecision(model="gpt-4o-mini", track=False),
        ],
        scoring_key_mapping={"input": "question"},
        experiment_name=experiment_name,
        experiment_config={"k": k, "model": "gpt-4o-mini"},
        task_threads=4,
    )
