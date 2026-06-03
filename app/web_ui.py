from __future__ import annotations

import argparse
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from llm_client import LlmError
from rag_bot import SupportRagBot
from retriever import KeywordRetriever


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WEB_DIR = PROJECT_ROOT / "web"
POLICY_PATH = PROJECT_ROOT / "data" / "policy.md"
BREAKER_QUESTIONS_PATH = PROJECT_ROOT / "data" / "breaker_questions.json"


class UiState:
    def __init__(self, model: str | None, base_url: str | None) -> None:
        self.model = model
        self.base_url = base_url
        self.retriever = KeywordRetriever.from_policy_file(POLICY_PATH)
        self.bot = SupportRagBot(model=model, base_url=base_url)


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    content_length = int(handler.headers.get("Content-Length", "0"))
    if content_length == 0:
        return {}
    body = handler.rfile.read(content_length).decode("utf-8")
    return json.loads(body)


def retrieval_payload(retriever: KeywordRetriever, question: str, top_k: int) -> dict[str, object]:
    chunks = retriever.search(question, top_k=top_k)
    return {
        "question": question,
        "retrieved_sections": [chunk.title for chunk in chunks],
        "context": "\n\n".join(f"[{chunk.title}]\n{chunk.text}" for chunk in chunks),
    }


def make_handler(state: UiState) -> type[BaseHTTPRequestHandler]:
    class WebUiHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            print(f"{self.client_address[0]} - {format % args}")

        def send_json(self, status: int, payload: dict[str, object]) -> None:
            body = json.dumps(payload, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_static(self, path: str) -> None:
            relative_path = "index.html" if path in {"", "/"} else unquote(path.lstrip("/"))
            file_path = (WEB_DIR / relative_path).resolve()

            if not str(file_path).startswith(str(WEB_DIR.resolve())) or not file_path.is_file():
                self.send_error(404, "File not found")
                return

            content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/api/breaker-questions":
                questions = json.loads(BREAKER_QUESTIONS_PATH.read_text(encoding="utf-8"))
                self.send_json(200, {"questions": questions})
                return

            if self.path == "/api/config":
                self.send_json(
                    200,
                    {
                        "model": state.bot.llm_client.model,
                        "base_url": state.bot.llm_client.base_url,
                    },
                )
                return

            self.send_static(self.path)

        def do_POST(self) -> None:
            if self.path not in {"/api/answer", "/api/retrieve"}:
                self.send_error(404, "Endpoint not found")
                return

            try:
                payload = read_json_body(self)
                question = str(payload.get("question", "")).strip()
                top_k = int(payload.get("top_k", 4))
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self.send_json(400, {"error": f"Invalid request body: {exc}"})
                return

            if not question:
                self.send_json(400, {"error": "Question is required."})
                return

            top_k = max(1, min(top_k, 8))

            if self.path == "/api/retrieve":
                self.send_json(200, retrieval_payload(state.retriever, question, top_k))
                return

            try:
                result = state.bot.answer(question, top_k=top_k)
            except LlmError as exc:
                self.send_json(
                    502,
                    {
                        "error": str(exc),
                        "retrieval": retrieval_payload(state.retriever, question, top_k),
                    },
                )
                return

            self.send_json(200, result)

    return WebUiHandler


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local browser UI for the AI evals demo.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--model", default=None)
    parser.add_argument("--base-url", default=None)
    args = parser.parse_args()

    if not WEB_DIR.exists():
        raise SystemExit(f"Missing UI directory: {WEB_DIR}")

    state = UiState(model=args.model, base_url=args.base_url)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(state))
    print(f"UI running at http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
