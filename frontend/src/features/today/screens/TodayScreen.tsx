import React, { useCallback, useMemo } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useFeed } from '@features/feed/hooks/useFeed';
import { CivicCardType, FeedItem } from '@features/feed/types';
import VotePromptForFeedItem from '@features/votes/components/VotePromptForFeedItem';
import { useUserPreferences } from '@context/UserPreferencesContext';
import { RootStackParamList } from '@navigation/RootNavigator';
import { useTheme } from '@theme/ThemeProvider';
import dayjs from '@utils/dayjs';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const cardTypeOrder: CivicCardType[] = ['vote', 'hearing', 'bill', 'alert', 'money'];
const cardTypeLabels: Record<CivicCardType, string> = {
  bill: 'Bills',
  vote: 'Votes',
  hearing: 'Hearings',
  money: 'Money',
  alert: 'Alerts',
};

const TodayScreen = () => {
  const { neutral, branch: branchColors, semantic } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const { preferences } = useUserPreferences();
  const feedOptions = useMemo(() => ({
    followedBills: preferences.followedBills,
    followedMembers: preferences.followedMembers,
    followedTopics: preferences.followedTopics,
    followedCommittees: preferences.followedCommittees,
    state: preferences.homeDistrict?.state,
    district: preferences.homeDistrict?.district,
    limit: 30,
  }), [preferences]);
  const { items, loading, error, reload } = useFeed('today', feedOptions);

  const grouped = useMemo(() => {
    return items.reduce<Record<string, FeedItem[]>>((acc, item) => {
      const key = item.card_type ?? 'alert';
      acc[key] = [...(acc[key] ?? []), item];
      return acc;
    }, {});
  }, [items]);

  const openItem = useCallback((item: FeedItem) => {
    navigation.navigate('UpdateDetail', { item });
  }, [navigation]);

  const topItem = items[0];

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={reload} tintColor={branchColors.agency} />
      }
    >
      <View style={styles.header}>
        <Text style={[styles.eyebrow, { color: neutral.textMuted }]}>
          {dayjs().format('dddd, MMMM D').toUpperCase()}
        </Text>
        <Text style={[styles.title, { color: neutral.textPrimary }]}>Today</Text>
      </View>

      {loading && items.length === 0 && (
        <View style={styles.stateBlock}>
          <ActivityIndicator size="large" color={branchColors.agency} />
          <Text style={[styles.stateText, { color: neutral.textSecondary }]}>
            Loading primary-source events...
          </Text>
        </View>
      )}

      {error && (
        <View style={[styles.notice, { borderColor: semantic.warning }]}>
          <Ionicons name="cloud-offline-outline" size={20} color={semantic.warning} />
          <Text style={[styles.noticeText, { color: neutral.textSecondary }]}>{error}</Text>
        </View>
      )}

      {!loading && items.length === 0 && (
        <View style={styles.stateBlock}>
          <Ionicons name="newspaper-outline" size={36} color={neutral.textMuted} />
          <Text style={[styles.stateText, { color: neutral.textSecondary }]}>
            No source-backed events are available for today yet.
          </Text>
        </View>
      )}

      {topItem && (
        <Pressable
          style={[styles.topStory, { backgroundColor: neutral.card, borderColor: neutral.divider }]}
          onPress={() => openItem(topItem)}
        >
          <View style={styles.topRow}>
            <Text style={[styles.sectionLabel, { color: branchColors.agency }]}>TOP RANKED EVENT</Text>
            <Text style={[styles.scoreText, { color: neutral.textMuted }]}>
              {Math.round(topItem.rank_context?.score ?? 0)}
            </Text>
          </View>
          <Text style={[styles.topHeadline, { color: neutral.textPrimary }]}>{topItem.headline}</Text>
          <Text style={[styles.summary, { color: neutral.textSecondary }]}>
            {topItem.summary ?? 'Official summary has not been published yet.'}
          </Text>
          <RankReasons item={topItem} />
          <SourceTrailPreview item={topItem} />
          <MoneyContextPreview item={topItem} />
          <VotePromptForFeedItem item={topItem} compact />
        </Pressable>
      )}

      {cardTypeOrder.map(cardType => {
        const sectionItems = grouped[cardType] ?? [];
        if (sectionItems.length === 0) return null;

        return (
          <View key={cardType} style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
                {cardTypeLabels[cardType]}
              </Text>
              <Text style={[styles.sectionCount, { color: neutral.textMuted }]}>
                {sectionItems.length}
              </Text>
            </View>

            {sectionItems.map(item => (
              <Pressable
                key={item.id}
                style={[styles.eventRow, { borderColor: neutral.divider, backgroundColor: neutral.card }]}
                onPress={() => openItem(item)}
              >
                <View style={styles.eventHeader}>
                  <Text style={[styles.eventType, { color: branchColors[item.branch] ?? branchColors.legislative }]}>
                    {(item.card_type ?? 'event').toUpperCase()}
                  </Text>
                  <Text style={[styles.eventTime, { color: neutral.textMuted }]}>
                    {dayjs(item.published_at).fromNow()}
                  </Text>
                </View>
                <Text style={[styles.eventHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                  {item.headline}
                </Text>
                {item.rank_context?.reasons?.[0] && (
                  <Text style={[styles.reasonText, { color: neutral.textSecondary }]} numberOfLines={2}>
                    {item.rank_context.reasons[0]}
                  </Text>
                )}
                <SourceTrailPreview item={item} compact />
                <MoneyContextPreview item={item} compact />
                <VotePromptForFeedItem item={item} compact />
              </Pressable>
            ))}
          </View>
        );
      })}
    </ScrollView>
  );
};

const RankReasons = ({ item }: { item: FeedItem }) => {
  const { neutral } = useTheme();
  const reasons = item.rank_context?.reasons ?? [];
  if (reasons.length === 0) return null;

  return (
    <View style={styles.reasonList}>
      {reasons.slice(0, 3).map(reason => (
        <View key={reason} style={styles.reasonRow}>
          <Ionicons name="information-circle-outline" size={16} color={neutral.textMuted} />
          <Text style={[styles.reasonText, { color: neutral.textSecondary }]}>{reason}</Text>
        </View>
      ))}
    </View>
  );
};

const SourceTrailPreview = ({ item, compact = false }: { item: FeedItem; compact?: boolean }) => {
  const { neutral, branch } = useTheme();
  const firstSource = item.source_trail?.[0];
  if (!firstSource && !item.source_trail_note) return null;

  return (
    <View style={compact ? styles.sourceCompact : styles.sourceBox}>
      <Ionicons
        name={firstSource ? 'link-outline' : 'alert-circle-outline'}
        size={16}
        color={firstSource ? branch.agency : neutral.textMuted}
      />
      <Text style={[styles.sourceText, { color: neutral.textSecondary }]} numberOfLines={compact ? 1 : 2}>
        {firstSource ? `${firstSource.label} · ${firstSource.source}` : item.source_trail_note}
      </Text>
    </View>
  );
};

const MoneyContextPreview = ({ item, compact = false }: { item: FeedItem; compact?: boolean }) => {
  const { neutral, branch } = useTheme();
  const status = item.money_context_status;
  if (!status || status === 'not_applicable') return null;

  const firstItem = item.money_context?.[0];
  const label = firstItem
    ? `${relationshipLabel(firstItem.source_relationship)}: ${firstItem.label}`
    : item.money_context_note;
  if (!label) return null;

  return (
    <View style={compact ? styles.sourceCompact : styles.sourceBox}>
      <Ionicons
        name={status === 'available' ? 'cash-outline' : 'alert-circle-outline'}
        size={16}
        color={status === 'available' ? branch.agency : neutral.textMuted}
      />
      <Text style={[styles.sourceText, { color: neutral.textSecondary }]} numberOfLines={compact ? 1 : 2}>
        {label}
      </Text>
    </View>
  );
};

const relationshipLabel = (relationship: string) => {
  switch (relationship) {
    case 'direct_source':
      return 'Direct source';
    case 'related_entity':
      return 'Related entity';
    case 'topic_context':
      return 'Topic context';
    default:
      return 'Unavailable';
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 60,
    paddingHorizontal: 16,
    paddingBottom: 120,
    gap: 16,
  },
  header: {
    gap: 4,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '700',
  },
  title: {
    fontSize: 34,
    fontWeight: '800',
  },
  stateBlock: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 48,
  },
  stateText: {
    fontSize: 15,
    textAlign: 'center',
  },
  notice: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  noticeText: {
    flex: 1,
    fontSize: 14,
  },
  topStory: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    gap: 10,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '800',
  },
  scoreText: {
    fontSize: 12,
    fontWeight: '700',
  },
  topHeadline: {
    fontSize: 22,
    lineHeight: 28,
    fontWeight: '800',
  },
  summary: {
    fontSize: 15,
    lineHeight: 22,
  },
  reasonList: {
    gap: 6,
  },
  reasonRow: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'flex-start',
  },
  reasonText: {
    flex: 1,
    fontSize: 13,
    lineHeight: 18,
  },
  sourceBox: {
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: 'rgba(148, 163, 184, 0.35)',
    paddingTop: 10,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  sourceCompact: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  sourceText: {
    flex: 1,
    fontSize: 12,
  },
  section: {
    gap: 10,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  sectionCount: {
    fontSize: 13,
    fontWeight: '700',
  },
  eventRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 14,
    gap: 8,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  eventType: {
    fontSize: 11,
    fontWeight: '800',
  },
  eventTime: {
    fontSize: 12,
  },
  eventHeadline: {
    fontSize: 16,
    lineHeight: 21,
    fontWeight: '700',
  },
});

export default TodayScreen;
