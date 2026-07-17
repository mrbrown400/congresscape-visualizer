import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@theme/ThemeProvider';
import dayjs from '@utils/dayjs';
import VotePromptForFeedItem from '@features/votes/components/VotePromptForFeedItem';
import { FeedItem } from '../types';

type Props = {
  item: FeedItem;
  onPress?: (item: FeedItem) => void;
  onSave?: (item: FeedItem) => void;
  isSaved?: boolean;
};

const FeedCard = ({ item, onPress, onSave, isSaved = false }: Props) => {
  const { branch, neutral } = useTheme();
  const accent = branch[item.branch] ?? branch.legislative;

  return (
    <Pressable
      onPress={() => onPress?.(item)}
      style={[
        styles.cardContainer,
        {
          backgroundColor: neutral.card,
          borderColor: neutral.divider,
        },
      ]}
    >
      <View style={[styles.accentRule, { backgroundColor: accent }]} />
      <View style={styles.cardContent}>
        <View style={styles.headerRow}>
          <View style={styles.metaRow}>
            <Text style={[styles.badgeText, { color: accent }]}>
              {(item.card_type ?? item.branch).toUpperCase()}
            </Text>
            <Text style={[styles.timeText, { color: neutral.textMuted }]}>
              {dayjs(item.published_at).fromNow()}
            </Text>
          </View>
          {onSave && (
            <Pressable onPress={() => onSave(item)} hitSlop={8} style={styles.iconButton}>
              <Ionicons
                name={isSaved ? 'bookmark' : 'bookmark-outline'}
                size={19}
                color={isSaved ? accent : neutral.textMuted}
              />
            </Pressable>
          )}
        </View>

        <Text style={[styles.headline, { color: neutral.textPrimary }]} numberOfLines={3}>
          {item.headline}
        </Text>
        <Text style={[styles.summary, { color: neutral.textSecondary }]} numberOfLines={2}>
          {item.summary ?? 'Official summary has not been published yet.'}
        </Text>

        {(item.body || item.jurisdiction || item.item_type) && (
          <Text style={[styles.localContext, { color: neutral.textMuted }]} numberOfLines={1}>
            {[item.body, item.jurisdiction, item.item_type].filter(Boolean).join(' · ').toUpperCase()}
          </Text>
        )}

        {item.source_trail_status && item.source_trail_status !== 'available' && (
          <Text style={[styles.sourceStatus, { color: neutral.textMuted }]}>
            {item.source_trail_status === 'pending' ? 'Official source trail pending.' : 'Official source trail unavailable.'}
          </Text>
        )}

        <VotePromptForFeedItem item={item} />
        <MoneyContextPreview item={item} />

        <View style={styles.footerRow}>
          <Text style={[styles.source, { color: neutral.textMuted }]}>
            {item.source.toUpperCase()}
          </Text>
          <View style={styles.tagRow}>
            {item.tags.slice(0, 2).map(tag => (
              <View key={tag} style={[styles.tagChip, { borderColor: neutral.divider }]}>
                <Text style={[styles.tagText, { color: neutral.textSecondary }]}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      </View>
    </Pressable>
  );
};

const MoneyContextPreview = ({ item }: { item: FeedItem }) => {
  const { neutral } = useTheme();
  if (!item.money_context_status || item.money_context_status === 'not_applicable') return null;
  const firstItem = item.money_context?.[0];
  const label = firstItem
    ? `${relationshipLabel(firstItem.source_relationship)}: ${firstItem.label}`
    : item.money_context_note;
  if (!label) return null;

  return (
    <View style={[styles.moneyPreview, { borderTopColor: neutral.divider }]}>
      <Text style={[styles.moneyPreviewText, { color: neutral.textSecondary }]} numberOfLines={2}>
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
  cardContainer: {
    marginBottom: 12,
    borderWidth: 1,
    borderRadius: 8,
    overflow: 'hidden',
  },
  accentRule: {
    height: 3,
  },
  cardContent: {
    padding: 16,
    gap: 10,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '800',
  },
  timeText: {
    fontSize: 12,
  },
  headline: {
    fontSize: 18,
    fontWeight: '800',
    lineHeight: 24,
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
  },
  localContext: {
    marginTop: 8,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
  },
  sourceStatus: {
    fontSize: 12,
    fontStyle: 'italic',
  },
  moneyPreview: {
    borderTopWidth: StyleSheet.hairlineWidth,
    paddingTop: 10,
  },
  moneyPreviewText: {
    fontSize: 13,
    lineHeight: 18,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  source: {
    fontSize: 12,
    fontWeight: '700',
    flexShrink: 0,
  },
  tagRow: {
    flexDirection: 'row',
    gap: 6,
    flexShrink: 1,
  },
  tagChip: {
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '600',
  },
  iconButton: {
    padding: 4,
  },
});

export default FeedCard;
