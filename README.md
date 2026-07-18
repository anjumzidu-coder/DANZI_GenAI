# Leadership Update Assistant (RAG)

A **Retrieval‑Augmented Generation (RAG)** project that helps produce
clear, leadership‑ready project updates from scattered project documents.

## Problem
In many teams, project information is fragmented across:
- status notes
- risk logs
- planning documents
- weekly updates

Leaders need:
- concise summaries
- clear risks & mitigations
- explicit decision asks

Generic LLMs often guess. This project uses **RAG** to ground answers in retrieved sources.

## Solution
This system retrieves relevant project content first, then generates
structured leadership updates with **citations**.

## What it supports
- Executive summary
- Risks & mitigations
- Leadership / decision asks
- Short talk tracks (60–90 seconds)
- Source grounding and citations

## Demo (CLI)
```bash
python apps/index_build.py
python apps/cli.py --question "What decision is required for Project Apollo?"
```

## Simple QA Demo (Fast Local Version)
This repository also includes a lightweight retrieval-first demo that is easy to run locally.

### Files
- `rag_demo.py`: terminal-based demo
- `web_demo.py`: browser-based demo
- `knowledge.txt`: small trusted knowledge base for answers

### Run CLI demo
```bash
python rag_demo.py
```

### Run web demo
```bash
python web_demo.py
```

Open this URL in your browser:

```text
http://127.0.0.1:8000
```

### Sample questions
- Who owns delivery readiness?
- What should happen before Plan Exit?
- When is the first service date?
