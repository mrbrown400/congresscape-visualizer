# M6 Database Migration Field Map

**Issues:** CON-53, CON-54

**Source baseline:** `main` at `f375c69`; current tables are created by `backend/app/db/init_db.py` and have no versioned migration history.

This map is deliberately additive. Existing columns remain readable until parity and rollback evidence allow a later cleanup migration.

## Field map

| Current table / fields | Generic target | Transform and null handling | Compatibility / rollback |
| --- | --- | --- | --- |
| `government_updates.external_id`, `source` | `policy_items.source_native_id`, `source_system`; `source_links` | Preserve both strings. Build `canonical_id` from jurisdiction + item kind + native ID; if missing, mark provisional instead of using the headline. | Keep the current `(external_id, source)` upsert key. A failed generic write leaves the legacy row available and is surfaced in the ingest batch diagnostics. |
| `government_updates.branch` | `policy_items.jurisdiction_key`, `government_bodies.body_type` | Map `house`/`senate` to `federal`; keep `branch` as a compatibility projection. `executive`, `judicial`, and `agency` remain valid source-native classifications. | Never use `branch` as the generic routing key. Preserve it until all old serializers stop reading it. |
| `government_updates.headline`, `summary`, `full_text` | `policy_items.title`, `summary`; `source_documents`/claims when full text is sourced | Copy title/summary. Treat blank full text as null, not an empty fact. Do not promote summary text to a canonical claim without source support. | Current feed payload is unchanged; rollback deletes no generic row and leaves the projection intact. |
| `government_updates.published_at`, `event_date` | `policy_items.published_at`, `PolicyAction.observed_at`/`effective_at` | Preserve source time separately from ingestion time. Missing event date stays null. | Existing feed ordering continues to use projection timestamps until generic parity is accepted. |
| `government_updates.url`, `metadata_json.source_url`, `metadata_json.source_trail` | `source_links` -> `document_versions` | Normalize URL strings; retain raw metadata and each source-trail entry. Missing URL becomes an explicit unavailable provenance state. | Existing provenance diagnostics continue reading the projection during dual-write. |
| `government_updates.bill_id`, `bill_action_id`, `vote_id`, `hearing_id` | Typed generic relationships: item/action/vote/meeting | Resolve only when the referenced federal row exists. Null remains null; never create a dangling generic reference. | Keep all four foreign keys and serializers during the transition. |
| `government_updates.tags`, `entities` | `policy_items.topic`/classification and typed entity relationships | Copy known controlled values; unresolved names become reviewable candidates, not automatic merges. | Existing tags/entity joins remain untouched. |
| `entities.name`, `type`, `slug`, `metadata_json` | `GovernmentBody`, `Official`, `Project`, `Geography`, or `entity_resolution_candidates` | Map only from explicit type rules and stable identifiers. Name-only rows remain unresolved. | Keep `entities` as a compatibility projection until entity resolution is complete. |
| `congressional_bills.canonical_id`, `congress`, `bill_type`, `number` | `policy_items.canonical_id`, source-native bill identity, federal extension | Use `us.federal:bill:{congress}-{bill_type}-{number}`. All source fields are required for a stable federal ID. | Preserve `CongressionalBill` as the federal projection and keep its unique constraint. |
| `congressional_bills.title`, `short_title`, `policy_area` | `policy_items.title`, `item_type`, `topic` | Copy title/short title; map policy area to a controlled topic only when recognized, otherwise preserve raw value. | No frontend field removal. |
| `congressional_bills.introduced_at`, `latest_action_at`, `latest_action_text` | `PolicyAction` history and lifecycle projection | `introduced_at` becomes an introduced action; latest action is one observed action only when it has a stable source identity. | Do not overwrite action history from a current summary field. |
| `congressional_bills.summaries`, `cosponsors`, `amendments`, `related_bills`, `subjects`, `cbo_cost_estimates`, `crs_reports` | Federal extension tables or typed relationships; `ExtractedClaim` where a claim is displayed | Preserve arrays as raw source payload during backfill. Promote only fields with an explicit generic relationship/claim contract. Empty arrays become empty collections. | Existing detail serializers remain the source of truth until generic detail parity. |
| `bill_actions.canonical_id`, `action_code`, `action_type`, `text`, `sequence` | `policy_actions` | Copy code/type/text/sequence. Missing action code is allowed only with a stable source record or deterministic provisional hash. | Keep the current unique action ID and bill FK. |
| `bill_actions.acted_at`, `chamber`, `committee_code`, `source_url` | `policy_actions.observed_at`, body relationship, `source_links` | Null chamber/committee/source remains null/unavailable; do not infer an actor from text. | Current action detail path remains intact. |
| `bill_text_versions.canonical_id`, `version_code`, `version_name`, `published_at`, `source_url`, `formats` | `source_documents` + immutable `document_versions` | Create one source identity and one version per distinct content hash/revision. Missing URL or date is retained as unavailable. | Keep the federal text row and link it to the version; never overwrite prior document bytes. |
| `congressional_committees.committee_code`, `name`, `chamber`, `committee_type`, `parent_committee_code` | `government_bodies` | Prefix federal source-native IDs and preserve parent hierarchy. Missing parent stays null. | Keep the projection and current committee code uniqueness. |
| `congressional_committees.jurisdiction`, `congress_url`, `metadata_json` | body description + `source_links` + raw source metadata | Copy text and source; retain raw payload for fields not yet modeled. | No change to current committee detail payload. |
| `congressional_members.bioguide_id`, `identifiers`, `name` | `officials` | Bioguide is the federal source-native identity. Preserve alternate identifiers; missing alternate IDs stay null. | Current member lookup continues to use the projection. |
| `congressional_members.party`, `state`, `district`, `chamber`, `member_type`, `current` | official role history + `geographies` | `current` becomes a validity projection; district is a time-bounded geography relationship. Null district is valid for senators. | Preserve member columns until all vote/detail consumers use generic roles. |
| `congressional_votes.canonical_id`, `chamber`, `congress`, `session`, `roll_number` | `votes` | Use the existing deterministic vote ID as source-native seed; preserve unknown session as explicit unknown. | Current vote unique/index constraints remain. |
| `congressional_votes.vote_date`, `question`, `result`, `totals`, `party_split`, `source_url` | `votes` + `source_links` | Copy dates/totals as source values; null result or source remains unavailable. | Existing vote detail serializer remains stable. |
| `member_vote_positions.vote_id`, `member_identifier`, `member_name`, `party`, `state`, `position` | `vote_positions` + `official` | Resolve official by stable identifier first. Unknown members remain positions with unresolved official references. | Keep the current composite uniqueness and raw position. |
| `congressional_hearings.canonical_id`, `event_id`, `congress`, `chamber`, `title` | `meetings` | Map event ID to a federal meeting ID; keep title/chamber/source-native fields. | Current hearing endpoint/detail payload remains unchanged. |
| `congressional_hearings.committee_id`, `meeting_type`, `status`, `scheduled_at`, `location` | meeting/body/status/time/location | Null values remain null; source-native status is retained beside generic lifecycle phase. | Keep federal committee FK and serializer. |
| `congressional_hearings.witnesses`, `related_bills`, `videos`, `transcripts` | `agenda_items`, typed item links, `document_versions`, source links | Preserve raw arrays; create typed links only when an identifier/source exists. | Existing hearing JSON remains readable during backfill. |
| `legislative_source_links.label`, `url`, `source_system` | `source_links` and `source_documents` | URL + source system identifies the source; label is display metadata. | Keep projection links and compare counts/source URLs. |
| `legislative_source_links.retrieved_at`, `published_at`, `confidence`, `source_category`, `supports` | provenance fields on `source_links`/`document_versions` | Copy exactly; missing published time stays null. Confidence/category values are validated against the current literals. | Existing source-trail labels remain unchanged. |
| `legislative_source_links.bill_id`, `action_id`, `text_version_id`, `committee_id`, `member_id`, `vote_id`, `hearing_id` | generic source subject references | Create only for non-null existing parents; orphan links are validation failures. | No source link deletion in backfill or rollback. |
| `district_lookup_results.lookup_key`, `lookup_type`, `query` | address-resolution record + geography resolution evidence | Keep lookup key/type; minimize raw query storage and never log raw addresses. | Current district lookup response remains compatible. |
| `district_lookup_results.state`, `district`, `source`, `retrieved_at`, `ambiguity_reason` | versioned geography resolution | Preserve source/vintage/time/ambiguity; no ZIP-only final mapping. | Existing federal district fields remain readable. |
| `district_lookup_results.representative_member_id`, `senator_member_ids`, `raw_response` | official/geography relationships + quarantined raw-source payload | Resolve only loaded current members; retain raw response outside the public contract. | Keep lookup cache and rollback by lookup batch. |
| `metadata_json` on all current models | raw source extension / migration audit payload | Preserve unknown source fields under a namespaced raw key; typed generic fields are authoritative after migration. | Never delete raw payload during backfill. |

## Null and compatibility rules

- Null means “not supplied or not applicable”; an explicit unavailable status is used when the source was checked and did not publish the value.
- Empty lists mean the source supplied no members/items in that collection; they do not mean “none exist” unless the source contract says so.
- Unknown source-native status is retained and mapped to generic `unknown`; it is never coerced to `implemented` or `closed`.
- Every backfill row carries `migration_batch_id`, `source_retrieved_at`, and `mapping_version`.
- Generic writes are idempotent on canonical/source identity. Re-running a batch updates projections but never deletes older document versions or source history.

## Validation queries

Run these after each batch against both SQLite and PostgreSQL equivalents:

```sql
-- Every federal projection has at most one generic identity.
SELECT COUNT(*) AS projection_rows,
       COUNT(DISTINCT canonical_id) AS distinct_ids
FROM congressional_bills;

-- No generic row is missing its source identity.
SELECT COUNT(*) AS missing_source_identity
FROM policy_items
WHERE source_system IS NULL OR source_native_id IS NULL;

-- No generic relationship points at a missing typed parent.
SELECT COUNT(*) AS orphan_actions
FROM policy_actions a
LEFT JOIN policy_items p ON p.id = a.policy_item_id
WHERE p.id IS NULL;

-- Source links with no valid source document or subject are quarantined.
SELECT COUNT(*) AS invalid_source_links
FROM source_links
WHERE document_version_id IS NULL OR subject_id IS NULL;

-- Dual-write parity is measured by source identity, not titles.
SELECT source_system, source_native_id, COUNT(*)
FROM policy_items
GROUP BY source_system, source_native_id
HAVING COUNT(*) > 1;
```

The exact table names may be adjusted by CON-55, but the invariants and query intent are fixed. Counts, unresolved mappings, duplicate candidates, orphan candidates, and source-link coverage are recorded per batch.

## Rollback notes

Rollback is a forward-safe disable: stop generic reads/writes, keep federal projections and current APIs active, quarantine the failed batch, and replay from source checkpoints. Do not drop generic tables, delete old source versions, or remove federal rows as part of rollback. A later destructive migration requires a separate reviewed migration with an explicit downgrade and backup restore test (`CON-54`, `CON-76`).
