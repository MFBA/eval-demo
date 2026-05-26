from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


STOPWORDS = {
    "a",
    "about",
    "after",
    "am",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "can",
    "do",
    "for",
    "from",
    "get",
    "i",
    "if",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "the",
    "to",
    "what",
    "when",
    "with",
    "you",
}


@dataclass(frozen=True)
class PolicyChunk:
    title: str
    text: str


def tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {word for word in words if word not in STOPWORDS}


def load_policy_chunks(policy_path: Path) -> list[PolicyChunk]:
    content = policy_path.read_text(encoding="utf-8")
    chunks: list[PolicyChunk] = []
    current_title = "Overview"
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_lines:
                chunks.append(
                    PolicyChunk(
                        title=current_title,
                        text="\n".join(current_lines).strip(),
                    )
                )
            current_title = line.removeprefix("## ").strip()
            current_lines = []
        elif line and not line.startswith("# "):
            current_lines.append(line)

    if current_lines:
        chunks.append(PolicyChunk(title=current_title, text="\n".join(current_lines).strip()))

    return chunks


class KeywordRetriever:
    def __init__(self, chunks: list[PolicyChunk]) -> None:
        self.chunks = chunks

    @classmethod
    def from_policy_file(cls, policy_path: Path) -> "KeywordRetriever":
        return cls(load_policy_chunks(policy_path))

    def search(self, question: str, top_k: int = 2) -> list[PolicyChunk]:
        query_tokens = tokenize(question)
        scored_chunks = []

        for chunk in self.chunks:
            title_tokens = tokenize(chunk.title)
            body_tokens = tokenize(chunk.text)
            title_score = len(query_tokens & title_tokens) * 3
            body_score = len(query_tokens & body_tokens)
            scored_chunks.append((title_score + body_score, chunk))

        scored_chunks.sort(key=lambda item: item[0], reverse=True)
        return [chunk for score, chunk in scored_chunks[:top_k] if score > 0]
