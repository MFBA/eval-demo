# RAG Bot Explainer

This project is a small customer support RAG bot for Northstar Outfitters, a fictional company.

The goal is to build a real, understandable AI app that can later be evaluated. It is not intentionally rigged to fail. Any failures should come from normal system behavior: imperfect retrieval, ambiguous policy language, prompt limitations, or model judgment.

## What The App Does

The bot answers customer support questions using a local policy document.

The flow is:

```text
Customer question -> Retriever -> Relevant policy sections -> LLM prompt -> Answer
```

## Files

```text
ai-evals-demo/
  app/
    llm_client.py     OpenAI chat-completions client using the standard library
    prompts.py        Grounding instructions and prompt builder
    rag_bot.py        CLI entry point and RAG orchestration
    retriever.py      Keyword retriever over policy sections
  data/
    policy.md         Fake company policy document
  EXPLAINER.md        This explainer
  README.md           Quickstart
```

## Policy Document

`data/policy.md` contains fictional policy rules for refunds, store credit, damaged items, international orders, gift cards, shipping, warranties, internal information, and override requests.

The policy is split by markdown headings. Each `##` section becomes one retrievable chunk.

## Retrieval

`app/retriever.py` loads the markdown policy and splits it into chunks.

The retriever uses simple keyword overlap:

1. Tokenize the customer question.
2. Tokenize each policy section title and body.
3. Score title matches higher than body matches.
4. Return the top matching sections.

This is intentionally simple, but not intentionally wrong. It is easy to explain and gives you a clean baseline before adding embeddings, reranking, metadata filters, or hybrid search.

## LLM Connection

`app/llm_client.py` calls an OpenAI-compatible chat completions API with `urllib`, so the demo does not require installing a Python package.

For this demo, it defaults to your LM Studio server:

```bash
http://127.0.0.1:1234
```

And this model:

```bash
google/gemma-3-1b
```

LM Studio usually does not require a real API key, so the client sends a placeholder key of `lm-studio` if `OPENAI_API_KEY` is not set.

You can override the model:

```bash
export OPENAI_MODEL="google/gemma-3-1b"
```

You can override the compatible API base URL:

```bash
export OPENAI_BASE_URL="http://127.0.0.1:1234"
```

## Prompting

`app/prompts.py` tells the model to:

- answer only from retrieved policy context
- say when the context is insufficient
- avoid inventing policy details
- reject unsupported exceptions
- distinguish cash refunds, replacements, and store credit
- refuse internal/private information
- mention supporting policy sections when possible

## Running It

From the project folder:

```bash
python3 app/rag_bot.py "Can I get a refund after 40 days?"
```

Pass LM Studio settings explicitly:

```bash
python3 app/rag_bot.py \
  --base-url http://127.0.0.1:1234 \
  --model google/gemma-3-1b \
  "Can I get a refund after 40 days?"
```

Show the retrieved context:

```bash
python3 app/rag_bot.py --show-context "Can I get a refund after 40 days?"
```

Change retrieval breadth:

```bash
python3 app/rag_bot.py --top-k 4 "Can I get a refund after 40 days?"
```

## Why This Is Useful For The Video

This gives you a real app loop before introducing evals:

1. A customer asks a question.
2. The retriever decides what policy evidence the model sees.
3. The LLM answers from that evidence.
4. Later evals can test answer correctness, retrieval quality, hallucination, refusal behavior, and prompt regressions.

That keeps the story grounded. You are not testing a fake response function. You are testing a small AI system.
