import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const frontendRoot = path.resolve(new URL('..', import.meta.url).pathname);
const outDir = mkdtempSync(path.join(tmpdir(), 'congresscape-vote-comparison-'));
const require = createRequire(import.meta.url);

try {
  execFileSync(
    'npx',
    [
      'tsc',
      '--target',
      'ES2020',
      '--module',
      'CommonJS',
      '--moduleResolution',
      'node',
      '--skipLibCheck',
      '--outDir',
      outDir,
      'src/features/votes/utils/voteComparison.ts',
    ],
    { cwd: frontendRoot, stdio: 'inherit' },
  );

  const comparison = require(path.join(outDir, 'voteComparison.js'));

  assert.equal(comparison.normalizeUserVotePosition('Yea'), 'yea');
  assert.equal(comparison.normalizeOfficialVotePosition('Not Voting'), 'not_voting');

  assert.deepEqual(comparison.compareVotePositions('yea', 'yea'), {
    status: 'aligned',
    userPosition: 'yea',
    officialPosition: 'yea',
    countsInDenominator: true,
    label: 'Aligned',
  });

  assert.equal(comparison.compareVotePositions('yea', 'nay').status, 'opposed');
  assert.equal(comparison.compareVotePositions('present', 'abstain').status, 'different');
  assert.equal(comparison.compareVotePositions('undecided', 'yea').countsInDenominator, false);
  assert.equal(comparison.compareVotePositions('yea', 'not voting').countsInDenominator, false);
  assert.equal(comparison.compareVotePositions(null, 'yea').status, 'missing_user');

  const summaries = comparison.summarizeVoteComparisons([
    {
      entityId: 'R000037',
      entityLabel: 'Representative',
      entityKind: 'member',
      voteId: 'vote-1',
      userPosition: 'yea',
      officialPosition: 'yea',
    },
    {
      entityId: 'R000037',
      entityLabel: 'Representative',
      entityKind: 'member',
      voteId: 'vote-2',
      userPosition: 'nay',
      officialPosition: 'yea',
    },
    {
      entityId: 'R000037',
      entityLabel: 'Representative',
      entityKind: 'member',
      voteId: 'vote-3',
      userPosition: 'undecided',
      officialPosition: 'nay',
    },
  ]);

  assert.equal(summaries[0].aligned, 1);
  assert.equal(summaries[0].opposed, 1);
  assert.equal(summaries[0].excluded, 1);
  assert.equal(summaries[0].comparable, 2);
  assert.equal(summaries[0].similarityPercent, 50);
  console.log('vote comparison tests passed');
} finally {
  rmSync(outDir, { recursive: true, force: true });
}
