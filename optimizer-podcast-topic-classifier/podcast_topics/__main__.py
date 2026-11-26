"""Score the baseline prompt on every labeled episode: python -m podcast_topics"""

import os

# Neutralize any local OpenAI proxy settings so the example talks to the public API.
os.environ.pop("OPENAI_BASE_URL", None)
os.environ.pop("OPENAI_API_BASE", None)

import dotenv
import opik

dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

from .classifier import classify
from .episodes import EPISODES
from .metric import topic_accuracy


def main() -> None:
    scores = []
    for blurb, label in EPISODES:
        answer = classify(blurb)
        score = topic_accuracy({"label": label}, answer)
        scores.append(score)
        print(f"{'ok ' if score else 'MISS'} [{label:10}] -> {answer[:60]!r}")
    print(f"\nbaseline accuracy: {sum(scores) / len(scores):.3f} on {len(scores)} episodes")
    # Traces are sent from a background thread; flush so none are lost at exit.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
