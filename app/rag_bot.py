from __future__ import annotations

import argparse
from pathlib import Path

from llm_client import LlmError, OpenAIChatClient
from prompts import SYSTEM_PROMPT, build_user_prompt
from retriever import KeywordRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = PROJECT_ROOT / "data" / "policy.md"


class SupportRagBot:
    def __init__(
        self,
        policy_path: Path = POLICY_PATH,
        llm_client: OpenAIChatClient | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.retriever = KeywordRetriever.from_policy_file(policy_path)
        self.llm_client = llm_client or OpenAIChatClient(model=model, base_url=base_url)
        self.system_prompt = SYSTEM_PROMPT

    def answer(self, question: str, top_k: int = 2) -> dict[str, object]:
        chunks = self.retriever.search(question, top_k=top_k)
        context = "\n\n".join(f"[{chunk.title}]\n{chunk.text}" for chunk in chunks)
        user_prompt = build_user_prompt(question=question, context=context)
        answer = self.llm_client.complete(system_prompt=self.system_prompt, user_prompt=user_prompt)

        return {
            "question": question,
            "answer": answer,
            "retrieved_sections": [chunk.title for chunk in chunks],
            "context": context,
            "system_prompt": self.system_prompt,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask the demo support RAG bot a question.")
    parser.add_argument("question", nargs="?", default="Can I get a refund after 40 days?")
    parser.add_argument("--top-k", type=int, default=2, help="Number of policy sections to retrieve.")
    parser.add_argument("--show-context", action="store_true", help="Print retrieved policy context.")
    parser.add_argument("--model", default=None, help="Chat model name. Defaults to OPENAI_MODEL or google/gemma-3-1b.")
    parser.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible base URL. Defaults to OPENAI_BASE_URL, LM_STUDIO_BASE_URL, or http://127.0.0.1:1234.",
    )
    args = parser.parse_args()

    try:
        bot = SupportRagBot(model=args.model, base_url=args.base_url)
        result = bot.answer(args.question, top_k=args.top_k)
    except LlmError as exc:
        raise SystemExit(f"LLM error: {exc}") from exc

    print(f"Question: {result['question']}")
    print(f"Answer: {result['answer']}")
    print(f"Retrieved sections: {', '.join(result['retrieved_sections']) or 'none'}")
    if args.show_context:
        print("\nRetrieved context:")
        print(result["context"] or "No context retrieved.")


if __name__ == "__main__":
    main()
