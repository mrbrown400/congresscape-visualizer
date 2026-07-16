# Production release checklist

This repository owns the application checks; managed database, hosting, secret, and billing resources are provisioned by the operator in the deployment environment.

## Before a release

- Run `npm run release:check` and `npm run quality` from the repository root.
- Run the backend health check and the Expo web/browser smoke flow against the release candidate.
- Build the backend image from `backend/Dockerfile` and verify the container starts with a managed `DATABASE_URL`.
- Apply schema initialization/migrations in a disposable environment first. Do not run destructive schema changes as part of an automatic deploy.
- Confirm `ENABLE_REALTIME=false` unless the keyed realtime source, quota, and cost owner are explicitly approved.

## Production configuration

- Do not use the sample postgres password from `docker-compose.yml`; use a managed database and secret injection.
- Set CORS to the deployed app origins, `DATABASE_URL` to the managed database, and API keys only in the secret store.
- Keep scheduled ingestion and push delivery bounded by the runtime locks, batch dedupe keys, and retry backoff.
- Keep a feature flag or forward-safe disable path for new source packages and realtime work.

## Backup and restore

- Enable managed database point-in-time recovery and a daily snapshot with a documented retention period.
- Before launch, restore the latest snapshot into an isolated database, initialize the application against it, and run the backend quality suite plus health check.
- Record snapshot ID, restore timestamp, schema version, row-count checks, and the operator who approved the restore.
- Run the deterministic manifest check described in [backup-restore-verification.md](backup-restore-verification.md) before approving the release.
- A rollback disables new writes or the affected feature and preserves source history; it does not delete prior documents or federal projections.

## Controlled live checks

- Start with one source package and one notification batch.
- Confirm source URL, retrieval timestamp, freshness diagnostics, and delivery dedupe behavior.
- Stop the check if authentication, quota, stale data, schema drift, or cost thresholds are exceeded.
