from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "app"
sys.path.insert(0, str(APP_DIR))

from llm_client import LlmError  # noqa: E402
from rag_bot import SupportRagBot  # noqa: E402
from retriever import KeywordRetriever  # noqa: E402


DEFAULT_QUESTIONS_PATH = PROJECT_ROOT / "data" / "breaker_questions.json"
POLICY_PATH = PROJECT_ROOT / "data" / "policy.md"


def load_questions(path: Path) -> list[dict[str, str]]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run breaker questions against the RAG bot.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--retrieval-only", action="store_true", help="Only show retrieved policy sections.")
    args = parser.parse_args()

    questions = load_questions(args.questions)
    retriever = KeywordRetriever.from_policy_file(POLICY_PATH)
    bot = None if args.retrieval_only else SupportRagBot(model=args.model, base_url=args.base_url)

    for index, case in enumerate(questions, start=1):
        print("=" * 88)
        print(f"{index}. {case['id']}")
        print(f"Question: {case['question']}")
        print(f"Expected: {case['expected_behavior']}")
        print(f"Why tricky: {case['why_it_breaks_bots']}")
        print()

        if args.retrieval_only:
            chunks = retriever.search(case["question"], top_k=args.top_k)
            print(f"Retrieved: {', '.join(chunk.title for chunk in chunks) or 'none'}")
        else:
            try:
                result = bot.answer(case["question"], top_k=args.top_k)
            except LlmError as exc:
                raise SystemExit(f"LLM error while running {case['id']}: {exc}") from exc

            print(f"Retrieved: {', '.join(result['retrieved_sections']) or 'none'}")
            print(f"Answer: {result['answer']}")
        print()


if __name__ == "__main__":
    main()
