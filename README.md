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
