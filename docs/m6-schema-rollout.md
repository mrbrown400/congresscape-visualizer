# M6 Schema Rollout and Verification Plan

**Issue:** CON-54

## Phases

1. **Baseline:** record the current Git SHA, database engine/version, table/row counts, unique constraints, source-trail counts, and the M1-M5 regression results.
2. **Additive schema:** create generic tables and indexes only. `Base.metadata.create_all` may initialize an empty test database, but production changes must use a versioned migration runner before any non-additive operation.
3. **Contract checks:** run model/schema tests for canonical IDs, null semantics, relationship FKs, source-link coverage, and immutable document hashes.
4. **Federal shadow write:** normalize existing federal fixtures into generic rows while keeping current federal writes and reads authoritative. Compare counts by `(source_system, source_native_id)` and canonical ID.
5. **Fixture local write:** persist one Metro board report, one City Council file, one meeting/vote, one funding authorization, one document revision, and one affected route without touching live government sources.
6. **Dual-read comparison:** run current and generic repositories for the same deterministic fixtures; log mismatches by field, relationship, source URL, and lifecycle stage.
7. **Per-surface cutover:** switch one API/service surface at a time behind a narrow repository selection. Keep projection writes until the surface has rollback evidence.
8. **Retirement gate:** remove or rename a federal projection only after parity, backup restore, regression, and rollback checks pass in both supported database engines.

## Required metrics

| Metric | Pass condition |
| --- | --- |
| Generic canonical-ID uniqueness | Zero duplicate canonical IDs. |
| Source identity uniqueness | Zero duplicate `(source_system, source_native_id, record_kind)` identities except explicitly versioned documents. |
| Orphan relationships | Zero orphan typed relationships; unresolved entities are quarantined with reason/method. |
| Provenance coverage | Every published policy/action/vote/meeting/funding claim has at least one source link or an explicit unavailable reason. |
| Document immutability | Same source bytes are idempotent; changed bytes create a new version; no prior version hash changes. |
| Federal parity | M1-M5 fixture counts, IDs, source URLs, and current frontend response shapes remain unchanged. |
| Local fixture coverage | Metro report, City file, meeting, vote, funding event, document revision, and route geography all persist and round-trip. |
| Rollback | Disabling generic reads restores current federal API behavior without deleting rows or source versions. |

## Operational checks

- Capture migration batch ID, code SHA, schema version, source retrieval timestamp, and database engine for every run.
- Run the field-map validation queries in `docs/m6-migration-field-map.md` before and after each batch.
- Fail closed on missing required source identity, duplicate canonical IDs, invalid foreign keys, or source-link orphans.
- Keep a quarantined mapping table/log for ambiguous or unresolved records; do not silently drop them or merge by display name.
- Confirm current `/api/v1/feed/`, `/api/v1/summary/`, `/api/v1/notifications/*`, and `/api/v1/members/district-lookup` behavior before and after any cutover.

## Rollback procedure

1. Disable the generic repository selector/feature flag.
2. Stop the generic writer or route the failed source package to quarantine.
3. Keep current federal projection writes and API reads active.
4. Preserve the failed batch, raw payloads, source links, document hashes, and diagnostics.
5. Restore from the last known-good backup only when schema state—not data mapping—is corrupt; verify restore before reopening writes.
6. Fix the mapper/schema, increment `mapping_version`, and replay idempotently from the source checkpoint.

Rollback must not delete federal projections, old document versions, or source history. Destructive downgrade and backup restore are separate release gates, not an automatic fallback.

## Verification commands

```bash
cd backend && PYTHONDONTWRITEBYTECODE=1 poetry run pytest tests/test_civic_core_models.py tests/test_legislative_m1.py tests/test_feed_m2.py -q -p no:cacheprovider
cd backend && poetry run ruff check app/models app/schemas tests/test_civic_core_models.py
cd frontend && npx tsc --noEmit
git diff --check
```

Browser smoke remains required when a later issue changes API serializers or navigation. This documentation issue itself has no runtime code change.
