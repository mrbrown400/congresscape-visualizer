export type UserVotePositionValue = 'yea' | 'nay' | 'present' | 'abstain' | 'undecided';

export type ComparableVotePosition = Exclude<UserVotePositionValue, 'undecided'>;

export type NormalizedOfficialVotePosition = ComparableVotePosition | 'not_voting' | 'unknown';

export type VoteComparisonStatus =
  | 'aligned'
  | 'opposed'
  | 'different'
  | 'missing_user'
  | 'missing_official'
  | 'excluded';

export type VoteComparisonResult = {
  status: VoteComparisonStatus;
  userPosition: UserVotePositionValue | null;
  officialPosition: NormalizedOfficialVotePosition | null;
  countsInDenominator: boolean;
  label: string;
};

export type VoteComparisonRecord = {
  entityId: string;
  entityLabel: string;
  entityKind: 'member' | 'party';
  entityMeta?: string | null;
  voteId: string;
  userPosition?: string | null;
  officialPosition?: string | null;
};

export type VoteComparisonSummary = {
  entityId: string;
  entityLabel: string;
  entityKind: 'member' | 'party';
  entityMeta?: string | null;
  aligned: number;
  different: number;
  opposed: number;
  excluded: number;
  comparable: number;
  total: number;
  similarityPercent: number | null;
};

const userPositionLabels: Record<UserVotePositionValue, string> = {
  yea: 'Yea',
  nay: 'Nay',
  present: 'Present',
  abstain: 'Abstain',
  undecided: 'Undecided',
};

export const getUserPositionLabel = (position?: string | null): string => {
  const normalized = normalizeUserVotePosition(position);
  return normalized ? userPositionLabels[normalized] : 'No position';
};

export const normalizeUserVotePosition = (position?: string | null): UserVotePositionValue | null => {
  const normalized = normalizeRawPosition(position);
  if (!normalized) return null;
  if (normalized === 'yes') return 'yea';
  if (normalized === 'no') return 'nay';
  if (isUserVotePosition(normalized)) return normalized;
  return null;
};

export const normalizeOfficialVotePosition = (
  position?: string | null,
): NormalizedOfficialVotePosition | null => {
  const normalized = normalizeRawPosition(position);
  if (!normalized) return null;
  if (normalized === 'yes') return 'yea';
  if (normalized === 'no') return 'nay';
  if (normalized === 'aye') return 'yea';
  if (normalized === 'noe') return 'nay';
  if (normalized === 'not-voting' || normalized === 'not voting' || normalized === 'nv') return 'not_voting';
  if (normalized === 'unknown') return 'unknown';
  if (isComparableVotePosition(normalized)) return normalized;
  if (normalized.includes('not') && normalized.includes('voting')) return 'not_voting';
  return 'unknown';
};

export const compareVotePositions = (
  userPosition?: string | null,
  officialPosition?: string | null,
): VoteComparisonResult => {
  const user = normalizeUserVotePosition(userPosition);
  const official = normalizeOfficialVotePosition(officialPosition);

  if (!user) {
    return {
      status: 'missing_user',
      userPosition: null,
      officialPosition: official,
      countsInDenominator: false,
      label: 'No personal position recorded',
    };
  }

  if (user === 'undecided') {
    return {
      status: 'excluded',
      userPosition: user,
      officialPosition: official,
      countsInDenominator: false,
      label: 'Undecided positions are excluded',
    };
  }

  if (!official) {
    return {
      status: 'missing_official',
      userPosition: user,
      officialPosition: null,
      countsInDenominator: false,
      label: 'Official member vote is unavailable',
    };
  }

  if (official === 'not_voting' || official === 'unknown') {
    return {
      status: 'excluded',
      userPosition: user,
      officialPosition: official,
      countsInDenominator: false,
      label: official === 'not_voting' ? 'Member did not vote' : 'Official vote is unclear',
    };
  }

  if (user === official) {
    return {
      status: 'aligned',
      userPosition: user,
      officialPosition: official,
      countsInDenominator: true,
      label: 'Aligned',
    };
  }

  if ((user === 'yea' && official === 'nay') || (user === 'nay' && official === 'yea')) {
    return {
      status: 'opposed',
      userPosition: user,
      officialPosition: official,
      countsInDenominator: true,
      label: 'Opposed',
    };
  }

  return {
    status: 'different',
    userPosition: user,
    officialPosition: official,
    countsInDenominator: true,
    label: 'Different',
  };
};

export const summarizeVoteComparisons = (
  records: VoteComparisonRecord[],
): VoteComparisonSummary[] => {
  const summaries = new Map<string, VoteComparisonSummary>();

  records.forEach(record => {
    const key = `${record.entityKind}:${record.entityId}`;
    const current = summaries.get(key) ?? {
      entityId: record.entityId,
      entityLabel: record.entityLabel,
      entityKind: record.entityKind,
      entityMeta: record.entityMeta,
      aligned: 0,
      different: 0,
      opposed: 0,
      excluded: 0,
      comparable: 0,
      total: 0,
      similarityPercent: null,
    };

    const comparison = compareVotePositions(record.userPosition, record.officialPosition);
    current.total += 1;

    if (!comparison.countsInDenominator) {
      current.excluded += 1;
    } else if (comparison.status === 'aligned') {
      current.aligned += 1;
      current.comparable += 1;
    } else if (comparison.status === 'opposed') {
      current.opposed += 1;
      current.comparable += 1;
    } else {
      current.different += 1;
      current.comparable += 1;
    }

    current.similarityPercent = current.comparable > 0
      ? Math.round((current.aligned / current.comparable) * 100)
      : null;
    summaries.set(key, current);
  });

  return Array.from(summaries.values()).sort((a, b) => {
    if (a.entityKind !== b.entityKind) return a.entityKind === 'member' ? -1 : 1;
    return (b.comparable - a.comparable) || a.entityLabel.localeCompare(b.entityLabel);
  });
};

const normalizeRawPosition = (position?: string | null): string | null => {
  if (!position) return null;
  return position.trim().toLowerCase().replace(/_/g, '-');
};

const isUserVotePosition = (position: string): position is UserVotePositionValue => {
  return ['yea', 'nay', 'present', 'abstain', 'undecided'].includes(position);
};

const isComparableVotePosition = (position: string): position is ComparableVotePosition => {
  return ['yea', 'nay', 'present', 'abstain'].includes(position);
};
