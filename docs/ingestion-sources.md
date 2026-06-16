# Ingestion Sources

This document outlines the primary data sources integrated into the ingestion pipeline and the purpose they serve. The M0 product posture is Congress.gov first: source-backed civic feed cards should prefer official APIs, preserve provenance, and expose clear unavailable states when official data is not present yet.

## Legislative Branch
- **Congress.gov API** – MVP backbone for bill lifecycle, actions, summaries, text versions, committees, cosponsors, amendments, related bills, subjects, committee meetings, hearings, votes, and member records.
- **Congress.gov pages** – Fallback source only when the API does not expose needed official detail.
- **usgpo/bill-status** (`govinfo.gov`) – Bulk bill status updates with actions, stages, and documents.
- **unitedstates/congress** – Legislator metadata (chambers, party, social handles) for entity resolution.

## Judicial Branch
- **Free Law Project / Juriscraper** – Supreme Court opinions, dockets, oral argument transcripts, and filings.
- **SCOTUSblog RSS (future)** – Rapid alerts for emergency orders and shadow docket activity.

## Executive Branch
- **Federal Register API** – Executive orders, rules, notices, presidential documents.
- **WhiteHouse.gov/presidential-actions** – Official statements, proclamations, memoranda, and executive actions.
- **GovInfo API** – Executive branch reports, budget documents, and agency publications.
- **api.data.gov** – Agency-specific press releases, data updates, program announcements.
- **SAM.gov Federal Hierarchy API** – Organizational graph to map agencies and bureaus.
- **Agency `data.json` indexes** – Discovery of distributed datasets and updates per agency.

## Money and Disclosure Context
- **CBO** – Cost estimates and budgetary effects for bills when published.
- **FEC/OpenFEC** – Campaign finance context for candidates, committees, and donors.
- **Lobbying Disclosure Act data** – Lobbying registrations and reports tied to organizations or issues.
- **USAspending.gov** – Federal award context for named organizations where a sourced relationship is supportable.
- **House/Senate financial disclosures and OGE** – Disclosure context when official records are available.

Money context must be labeled by source relationship: direct source match, related entity match, topic/industry context, or unavailable. It must not imply corruption, motive, or intent.

## Ingestion Workflow
1. **Fetch** raw payloads via async HTTP clients or Juriscraper scrapers.
2. **Normalize** into `NormalizedUpdate` dataclasses with consistent fields.
3. **Preserve provenance** with source URLs, labels, retrieval timestamps, and the claim IDs each source supports.
4. **Enrich** with summaries, vector embeddings, entity resolution, and money context only when the source relationship is clear.
5. **Persist** via `UpdateService` and future canonical civic-domain services.

Each source module exports async generators returning normalized updates; the orchestration layer (`app.ingest.runner`) schedules these generators and routes them through the `IngestPipeline` service.
