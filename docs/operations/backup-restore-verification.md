# Backup and restore verification

`backend/app/services/backup_restore.py` provides the deterministic manifest check used by the test suite. A manifest records a snapshot ID, schema digest, per-table row counts, and a canonical row digest. The verifier fails when schema, counts, or row content drift after restore.

The production operator still needs to run a managed-database restore into an isolated database. Record the provider snapshot ID, restore timestamp, schema version, row-count comparison, `npm run quality` result, and approval owner in the release record. Never test restore by overwriting the production database.
