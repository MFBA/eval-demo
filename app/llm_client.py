from __future__ import annotations

import json
import os
import urllib.error
import urllib.request


class LlmError(RuntimeError):
    pass


def normalize_openai_base_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1"


class OpenAIChatClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: int = 45,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or "lm-studio"
        self.model = model or os.getenv("OPENAI_MODEL", "google/gemma-3-1b")
        configured_base_url = (
            base_url
            or os.getenv("OPENAI_BASE_URL")
            or os.getenv("LM_STUDIO_BASE_URL")
            or "http://127.0.0.1:1234"
        )
        self.base_url = normalize_openai_base_url(configured_base_url)
        self.timeout_seconds = timeout_seconds

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            raise LlmError(f"OpenAI API request failed with HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            raise LlmError(f"OpenAI API request failed: {exc.reason}") from exc

        try:
            return data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise LlmError(f"Unexpected OpenAI API response: {data}") from exc
