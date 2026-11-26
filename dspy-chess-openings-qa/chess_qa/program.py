"""The DSPy program: a ChainOfThought over the opening cards."""

import dspy
import opik

from .tracing import PROJECT_NAME


class OpeningQA(dspy.Signature):
    """Answer the coach's question using the opening cards."""

    context: str = dspy.InputField(desc="the club's opening cards")
    question: str = dspy.InputField()
    answer: str = dspy.OutputField()


# The signature says nothing about the house answer format, so the raw program
# answers in ordinary prose. Only compiled demos can teach the convention.
def build_program() -> dspy.Module:
    return dspy.ChainOfThought(OpeningQA)


# track opens a general-type root span, so the DSPy callback spans nest under one
# named "ask_coach" trace instead of each module call becoming its own trace.
# project_name is explicit: the decorator resolves its project when opik is imported,
# so a later os.environ assignment would leave this trace in "Default Project".
@opik.track(name="ask_coach", type="general", project_name=PROJECT_NAME)
def ask(program: dspy.Module, context: str, question: str) -> str:
    return program(context=context, question=question).answer
