"""Trace the handbook assistant in Opik, then compare retrieval depth k=1 vs k=3 in two experiments."""

import os

PROJECT_NAME = "langgraph-stargazing-rag"
# Must be set before opik is imported so every trace lands in this project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import dotenv

dotenv.load_dotenv()
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

import opik
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from opik.integrations.langchain import OpikTracer, track_langgraph

from evaluation import get_dataset, run_experiment
from rag import build_app

QUESTIONS = [
    "How long does the 200 mm Dobsonian need to cool down?",
    "Which night of the year is the star party open to guests?",
    "Can I buy a telescope through the club?",
]


def make_traced_app(k: int):
    app = build_app(OpenAIEmbeddings(model="text-embedding-3-small"),
                    ChatOpenAI(model="gpt-4o-mini", temperature=0), k=k)
    # track_langgraph attaches an OpikTracer to the compiled graph: each invoke() becomes one
    # trace, each node a span, and the ChatOpenAI call an llm span with tokens and cost.
    # The k tag marks these demo traces; experiment traces carry k in the experiment config.
    return track_langgraph(app, OpikTracer(project_name=PROJECT_NAME, tags=[f"k={k}"]))


def main() -> None:
    demo_app = make_traced_app(k=3)
    for question in QUESTIONS:
        result = demo_app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")

    dataset = get_dataset(opik.Opik(project_name=PROJECT_NAME))
    for k in (1, 3):
        evaluation = run_experiment(dataset, make_traced_app(k), f"retrieval-k{k}", k)
        scores = evaluation.aggregate_evaluation_scores().aggregated_scores
        summary = ", ".join(f"{name}={stats.mean:.2f}" for name, stats in scores.items())
        print(f"retrieval-k{k}: {summary}\n  {evaluation.experiment_url}")

    # Traces and scores are sent from background threads; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
