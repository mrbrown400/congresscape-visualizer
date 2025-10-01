# Ingestion Sources

This document outlines the primary data sources integrated into the ingestion pipeline and the purpose they serve.

## Legislative Branch
- **usgpo/bill-status** (`govinfo.gov`) – Bulk bill status updates with actions, stages, and documents.
- **Congress.gov API** – Latest bill movements, summaries, committee reports, and cosponsor changes.
- **unitedstates/congress** – Legislator metadata (chambers, party, social handles) for entity resolution.

## Judicial Branch
- **Free Law Project / Juriscraper** – Supreme Court opinions, dockets, oral argument transcripts, and filings.
- **SCOTUSblog RSS (future)** – Rapid alerts for emergency orders and shadow docket activity.

## Executive Branch
- **Federal Register API** – Executive orders, rules, notices, presidential documents.
- **WhiteHouse.gov/presidential-actions** – Vacuum of statements, proclamations, memoranda.
- **GovInfo API** – Executive branch reports, budget documents, and agency publications.
- **api.data.gov** – Agency-specific press releases, data updates, program announcements.
- **SAM.gov Federal Hierarchy API** – Organizational graph to map agencies and bureaus.
- **Agency `data.json` indexes** – Discovery of distributed datasets and updates per agency.

## Ingestion Workflow
1. **Fetch** raw payloads via async HTTP clients or Juriscraper scrapers.
2. **Normalize** into `NormalizedUpdate` dataclasses with consistent fields.
3. **Enrich** with LLM summaries, vector embeddings, entity resolution.
4. **Persist** via `UpdateService` into PostgreSQL/pgvector.

Each source module exports async generators returning normalized updates; the orchestration layer (`app.ingest.runner`) schedules these generators and routes them through the `IngestPipeline` service.
