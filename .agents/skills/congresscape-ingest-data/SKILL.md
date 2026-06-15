---
name: congresscape-ingest-data
description: Use for Congress, executive, judicial, summary, embedding, and data provenance work.
---

# Congresscape Ingest Data

Use this skill for ingestion connectors, normalization, enrichment, summaries, and government data provenance.

## Rules

- Keep branch values consistent with `BranchEnum`.
- Keep raw-source provenance in metadata where schemas support it.
- Separate published updates from future events with `published_at` and `event_date`.
- Do not make live network calls in tests without an explicit integration-test scope.
- Be clear when a source is a placeholder, fallback, or reference entry.
- Do not compute paid LLM summaries or embeddings unless persistence and value are clear.

## Common Owners

- Shared shape: `backend/app/ingest/base.py`
- Legislative: `backend/app/ingest/congress.py`
- Executive: `backend/app/ingest/executive.py`
- Judicial: `backend/app/ingest/judicial.py`
- Pipeline: `backend/app/services/ingest_pipeline.py`
- Persistence: `backend/app/services/update_service.py`
- Daily summary: `backend/app/services/daily_summary_service.py`

## Verification

Run targeted backend tests first. For live source checks, record the URL/source, date, and any network or credential requirements.
