import React, { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useUserPreferences } from '@context/UserPreferencesContext';
import { VotePosition } from '@features/feed/types';
import { useTheme } from '@theme/ThemeProvider';
import {
  VoteComparisonRecord,
  compareVotePositions,
  getUserPositionLabel,
  summarizeVoteComparisons,
} from '../utils/voteComparison';
import { VoteSubject, findLedgerEntry } from '../utils/voteSubjects';

type Props = {
  subject: VoteSubject;
  positions: VotePosition[];
  localPositions?: VotePosition[];
  title?: string;
};

const VoteComparisonPanel = ({
  subject,
  positions,
  localPositions = [],
  title = 'Vote Comparison',
}: Props) => {
  const { neutral, branch } = useTheme();
  const { preferences } = useUserPreferences();
  const saved = findLedgerEntry(preferences.billPositions, subject.subjectId, subject.voteId);
  const selectedMemberIds = useMemo(() => new Set([
    ...preferences.currentMembers.map(member => member.bioguide_id),
    ...preferences.followedMembers,
  ]), [preferences.currentMembers, preferences.followedMembers]);

  const selectedRows = useMemo(() => {
    const rows = new Map<string, VotePosition>();
    localPositions.forEach(position => rows.set(position.member_identifier, position));
    positions.forEach(position => {
      if (selectedMemberIds.has(position.member_identifier)) {
        rows.set(position.member_identifier, position);
      }
    });
    return Array.from(rows.values());
  }, [localPositions, positions, selectedMemberIds]);

  const partySummaries = useMemo(() => {
    if (!saved) return [];
    const records: VoteComparisonRecord[] = positions
      .filter(position => Boolean(position.party))
      .map(position => ({
        entityId: position.party ?? 'Unknown',
        entityLabel: `${position.party ?? 'Unknown'} party`,
        entityKind: 'party',
        entityMeta: 'Official member positions on this roll call',
        voteId: subject.voteId ?? subject.subjectId,
        userPosition: saved.position,
        officialPosition: position.position,
      }));
    return summarizeVoteComparisons(records).slice(0, 4);
  }, [positions, saved, subject.subjectId, subject.voteId]);

  return (
    <View style={[styles.container, { borderColor: neutral.divider }]}>
      <Text style={[styles.title, { color: neutral.textMuted }]}>{title.toUpperCase()}</Text>
      {!saved ? (
        <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>
          Record a personal position to compare it with official member votes.
        </Text>
      ) : positions.length === 0 ? (
        <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>
          Your position is {getUserPositionLabel(saved.position)}. Official member positions are not published yet.
        </Text>
      ) : (
        <>
          <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>
            Your position is {getUserPositionLabel(saved.position)}. Denominators exclude undecided personal positions, missing official votes, and non-voting/unknown member records.
          </Text>

          {selectedRows.length > 0 && (
            <View style={styles.stack}>
              <Text style={[styles.subhead, { color: neutral.textPrimary }]}>Representatives And Followed Members</Text>
              {selectedRows.map(position => (
                <MemberComparisonRow
                  key={position.member_identifier}
                  userPosition={saved.position}
                  position={position}
                />
              ))}
            </View>
          )}

          {partySummaries.length > 0 && (
            <View style={styles.stack}>
              <Text style={[styles.subhead, { color: neutral.textPrimary }]}>Party Position Similarity</Text>
              {partySummaries.map(summary => (
                <View key={`${summary.entityKind}-${summary.entityId}`} style={[styles.summaryRow, { borderColor: neutral.divider }]}>
                  <View style={styles.summaryText}>
                    <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{summary.entityLabel}</Text>
                    <Text style={[styles.metaText, { color: neutral.textMuted }]}>
                      {summary.comparable} comparable, {summary.excluded} excluded
                    </Text>
                  </View>
                  <Text style={[styles.score, { color: branch.agency }]}>
                    {summary.similarityPercent === null ? 'N/A' : `${summary.similarityPercent}%`}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </>
      )}
    </View>
  );
};

const MemberComparisonRow = ({
  userPosition,
  position,
}: {
  userPosition: string;
  position: VotePosition;
}) => {
  const { neutral, branch } = useTheme();
  const comparison = compareVotePositions(userPosition, position.position);
  return (
    <View style={[styles.summaryRow, { borderColor: neutral.divider }]}>
      <View style={styles.summaryText}>
        <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{position.member_name}</Text>
        <Text style={[styles.metaText, { color: neutral.textMuted }]}>
          {[position.party, position.state, position.district ? `District ${position.district}` : null].filter(Boolean).join(' · ')}
        </Text>
      </View>
      <View style={styles.badgeGroup}>
        <Text style={[styles.badge, { color: branch.agency }]}>{position.position.toUpperCase()}</Text>
        <Text style={[styles.statusText, { color: neutral.textMuted }]}>{comparison.label}</Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    gap: 10,
  },
  title: {
    fontSize: 12,
    fontWeight: '800',
  },
  subhead: {
    fontSize: 14,
    fontWeight: '800',
  },
  stack: {
    gap: 8,
  },
  bodyText: {
    fontSize: 14,
    lineHeight: 20,
  },
  bodyTextStrong: {
    fontSize: 14,
    lineHeight: 20,
    fontWeight: '700',
  },
  metaText: {
    fontSize: 12,
    lineHeight: 17,
  },
  summaryRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 10,
  },
  summaryText: {
    flex: 1,
    gap: 3,
  },
  score: {
    fontSize: 15,
    fontWeight: '800',
  },
  badgeGroup: {
    alignItems: 'flex-end',
    gap: 3,
  },
  badge: {
    fontSize: 12,
    fontWeight: '800',
  },
  statusText: {
    fontSize: 11,
    fontWeight: '700',
  },
});

export default VoteComparisonPanel;
