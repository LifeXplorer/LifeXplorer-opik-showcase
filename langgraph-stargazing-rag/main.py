"""Ask the handbook assistant a few questions."""

import dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from rag import build_app

dotenv.load_dotenv()
dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))

QUESTIONS = [
    "How long does the 200 mm Dobsonian need to cool down?",
    "Which night of the year is the star party open to guests?",
    "Can I buy a telescope through the club?",
]


def make_app(k: int):
    return build_app(OpenAIEmbeddings(model="text-embedding-3-small"),
                     ChatOpenAI(model="gpt-4o-mini", temperature=0), k=k)


def main() -> None:
    app = make_app(k=3)
    for question in QUESTIONS:
        result = app.invoke({"question": question})
        print(f"Q: {question}\nA: {result['answer']}\n")


if __name__ == "__main__":
    main()
