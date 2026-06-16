import React from 'react';
import { GestureResponderEvent, Pressable, StyleSheet, Text, View } from 'react-native';

import { useUserPreferences, UserBillPosition } from '@context/UserPreferencesContext';
import { useTheme } from '@theme/ThemeProvider';
import { UserVotePositionValue, getUserPositionLabel } from '../utils/voteComparison';
import { VoteSubject, findLedgerEntry, localVotePrivacyCopy } from '../utils/voteSubjects';

const positionOptions: { value: UserVotePositionValue; label: string }[] = [
  { value: 'yea', label: 'Yea' },
  { value: 'nay', label: 'Nay' },
  { value: 'present', label: 'Present' },
  { value: 'abstain', label: 'Abstain' },
  { value: 'undecided', label: 'Undecided' },
];

type Props = {
  subject: VoteSubject;
  compact?: boolean;
  showPrompt?: boolean;
};

const UserVotePositionControl = ({ subject, compact = false, showPrompt = true }: Props) => {
  const { neutral, branch } = useTheme();
  const { preferences, setBillPosition, clearBillPosition } = useUserPreferences();
  const saved = findLedgerEntry(preferences.billPositions, subject.subjectId, subject.voteId);

  const handleSet = (event: GestureResponderEvent, position: UserVotePositionValue) => {
    event.stopPropagation();
    setBillPosition(subject.subjectId, position, {
      voteId: subject.voteId,
      sourceUrl: subject.sourceUrl,
      label: subject.label,
      prompt: subject.prompt,
    });
  };

  const handleClear = (event: GestureResponderEvent) => {
    event.stopPropagation();
    clearBillPosition(saved?.billId ?? subject.subjectId);
  };

  return (
    <View
      style={[
        styles.container,
        compact && styles.containerCompact,
        { borderColor: compact ? 'rgba(255,255,255,0.2)' : neutral.divider },
      ]}
    >
      {showPrompt && (
        <Text style={[styles.prompt, compact ? styles.promptCompact : null, { color: compact ? '#F8FAFC' : neutral.textSecondary }]}>
          {subject.prompt}
        </Text>
      )}
      <View style={styles.positionGrid}>
        {positionOptions.map(option => {
          const active = saved?.position === option.value;
          return (
            <Pressable
              key={option.value}
              style={[
                styles.positionButton,
                compact && styles.positionButtonCompact,
                {
                  borderColor: active ? branch.agency : (compact ? 'rgba(255,255,255,0.34)' : neutral.divider),
                  backgroundColor: active ? branch.agency : (compact ? 'rgba(255,255,255,0.12)' : neutral.card),
                },
              ]}
              onPress={event => handleSet(event, option.value)}
            >
              <Text style={[styles.positionText, { color: active || compact ? '#FFFFFF' : neutral.textPrimary }]}>
                {option.label}
              </Text>
            </Pressable>
          );
        })}
      </View>
      <View style={styles.footerRow}>
        <Text style={[styles.privacyText, compact ? styles.privacyTextCompact : null, { color: compact ? '#E2E8F0' : neutral.textMuted }]}>
          {saved ? `Recorded ${formatSavedPosition(saved)}. ` : ''}{localVotePrivacyCopy}
        </Text>
        {saved && (
          <Pressable onPress={handleClear}>
            <Text style={[styles.clearText, { color: compact ? '#FFFFFF' : branch.agency }]}>
              Clear
            </Text>
          </Pressable>
        )}
      </View>
    </View>
  );
};

const formatSavedPosition = (saved: UserBillPosition) => {
  return `${getUserPositionLabel(saved.position)} ${new Date(saved.updatedAt).toLocaleDateString()}`;
};

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    gap: 8,
  },
  containerCompact: {
    padding: 8,
  },
  prompt: {
    fontSize: 14,
    lineHeight: 20,
  },
  promptCompact: {
    fontSize: 12,
    lineHeight: 17,
  },
  positionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  positionButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  positionButtonCompact: {
    paddingHorizontal: 8,
    paddingVertical: 5,
  },
  positionText: {
    fontSize: 12,
    fontWeight: '800',
  },
  footerRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  privacyText: {
    flex: 1,
    fontSize: 12,
    lineHeight: 17,
  },
  privacyTextCompact: {
    fontSize: 11,
    lineHeight: 15,
  },
  clearText: {
    fontSize: 12,
    fontWeight: '800',
  },
});

export default UserVotePositionControl;
