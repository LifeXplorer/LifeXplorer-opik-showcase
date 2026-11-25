"""Ask the syllabi a few policy questions and print the answers with their sources."""

import dotenv

dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True))  # walks up to a repo-root .env if there is one

from syllabus_qa import engine, questions  # noqa: E402


def main() -> None:
    query_engine = engine.build_query_engine()
    for question in questions.DEMO_QUESTIONS:
        answer = engine.ask(query_engine, question)
        print(f"Q: {question}\nA: {answer.text}")
        print("   sources: " + ", ".join(f"{s['file']} ({s['score']})" for s in answer.sources) + "\n")


if __name__ == "__main__":
    main()
