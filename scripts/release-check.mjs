import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const files = {
  package: await readFile(resolve(root, 'package.json'), 'utf8'),
  compose: await readFile(resolve(root, 'docker-compose.yml'), 'utf8'),
  env: await readFile(resolve(root, 'backend/.env.example'), 'utf8'),
  settings: await readFile(resolve(root, 'backend/app/core/config.py'), 'utf8'),
  operations: await readFile(resolve(root, 'docs/operations/release-checklist.md'), 'utf8'),
};

const checks = [
  ['quality command is defined', files.package.includes('"quality":')],
  ['release checklist is tracked', files.operations.includes('Backup and restore') && files.operations.includes('backup-restore-verification.md')],
  ['database has a healthcheck', files.compose.includes('pg_isready')],
  ['database data uses a named volume', files.compose.includes('pgdata:')],
  ['backend waits for a healthy database', files.compose.includes('condition: service_healthy')],
  ['database configuration is environment-driven', files.env.includes('DATABASE_URL=')],
  ['realtime is opt-in by default', files.settings.includes('enable_realtime: bool = False')],
  ['production secrets are called out', files.operations.includes('Do not use the sample postgres password')],
];

for (const [label, passed] of checks) console.log(`${passed ? 'PASS' : 'FAIL'} ${label}`);
if (checks.some(([, passed]) => !passed)) process.exitCode = 1;
