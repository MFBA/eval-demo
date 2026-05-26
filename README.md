# AI Evals Demo

This is a tiny fictional customer support RAG app for a video about moving from vibe-checking AI to measuring AI behavior.

The app is intentionally simple:

- `data/policy.md` contains fake company rules.
- `app/retriever.py` does keyword-based retrieval over policy sections.
- `app/llm_client.py` calls the OpenAI chat completions API.
- `app/rag_bot.py` retrieves policy context and asks the LLM to answer from it.
- `app/prompts.py` contains the grounding instructions.

By default, this project is configured for the LM Studio server running at:

```bash
http://127.0.0.1:1234
```

With this model:

```bash
google/gemma-3-1b
```

Run the demo:

```bash
cd ai-evals-demo
python3 app/rag_bot.py "Can I get a refund after 40 days?"
python3 app/rag_bot.py --show-context "Can I get a refund after 40 days?"
```

You can also pass the LM Studio settings explicitly:

```bash
python3 app/rag_bot.py \
  --base-url http://127.0.0.1:1234 \
  --model google/gemma-3-1b \
  "Can I get a refund after 40 days?"
```

LM Studio usually accepts a placeholder API key, so this project defaults to `lm-studio` when `OPENAI_API_KEY` is not set.

Read `EXPLAINER.md` for the architecture and how the pieces fit together.

Run the breaker-question set:

```bash
python3 evals/run_breaker_questions.py
```

The breaker questions live in `data/breaker_questions.json`.
