"""Exact-match accuracy for the topic label."""


def normalize(answer: str) -> str:
    """Lowercase and strip quotes and punctuation, so "Science." passes but "It's science" does not."""
    return answer.strip().lower().strip(".!\"'` *")


def topic_accuracy(dataset_item: dict, llm_output: str) -> float:
    """1.0 if the model's whole answer is the labeled topic, else 0.0."""
    return 1.0 if normalize(llm_output) == dataset_item["label"] else 0.0
