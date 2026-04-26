# DANZI GenAI — NSI Leadership RAG Assistant

A **Retrieval-Augmented Generation (RAG)** project that turns scattered NSI notes into **leadership-ready updates** — grounded in retrieved sources with citations.

## Why this exists
In delivery readiness work, information is spread across notes, emails, and documents.
Leadership needs **decision-oriented updates**:
- Executive summary
- Risks & dependencies (with mitigation + owner)
- Leadership asks
- 60–90 sec talk track

A vanilla LLM guesses. RAG retrieves verified context first, then generates a grounded response.

## What it does (MVP)
- Ingests NSI documents (synthetic, GitHub-safe)
- Chunks + embeds content into a local vector store
- Retrieves relevant chunks for a question
- Generates a leadership-style answer **with citations**
- Includes a basic evaluation dataset for retrieval quality

## Demo (CLI)
```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt

# Build index
python apps/index_build.py

# Ask questions (leadership mode)
python apps/cli.py --question "What is the leadership ask for NSI 823?"
python apps/cli.py --question "List risks and mitigations for NSI 826"
python apps/cli.py --question "Give me a 60-90 sec talk track for NSI 823"
