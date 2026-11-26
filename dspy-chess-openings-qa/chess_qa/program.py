"""The DSPy program: a ChainOfThought over the opening cards."""

import dspy


class OpeningQA(dspy.Signature):
    """Answer the coach's question using the opening cards."""

    context: str = dspy.InputField(desc="the club's opening cards")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


# The signature says nothing about the house answer format, so the raw program
# answers in ordinary prose. Only compiled demos can teach the convention.
def build_program() -> dspy.Module:
    return dspy.ChainOfThought(OpeningQA)
