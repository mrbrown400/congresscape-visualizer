import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@theme/ThemeProvider';
import { FeedItem, Branch } from '@features/feed/types';
import dayjs from '@utils/dayjs';

const branchConfig: Record<string, { icon: keyof typeof Ionicons.glyphMap; label: string }> = {
  legislative: { icon: 'business', label: 'Legislative' },
  house: { icon: 'business', label: 'House' },
  senate: { icon: 'business', label: 'Senate' },
  executive: { icon: 'document-text', label: 'Executive' },
  judicial: { icon: 'scale', label: 'Judicial' },
  agency: { icon: 'grid', label: 'Agency' },
};

type Props = {
  item: FeedItem;
  onPress?: (item: FeedItem) => void;
  onSave?: (item: FeedItem) => void;
  isSaved?: boolean;
  compact?: boolean;
};

const UpdateCard = ({ item, onPress, onSave, isSaved = false, compact = false }: Props) => {
  const { branch: branchColors, neutral } = useTheme();

  const branchColor = branchColors[item.branch as Branch] || branchColors.legislative;
  const config = branchConfig[item.branch] || branchConfig.legislative;

  if (compact) {
    return (
      <Pressable
        style={[styles.compactContainer, { backgroundColor: neutral.card }]}
        onPress={() => onPress?.(item)}
      >
        <View style={[styles.compactBar, { backgroundColor: branchColor }]} />
        <View style={styles.compactContent}>
          <Text style={[styles.compactHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
            {item.headline}
          </Text>
          <View style={styles.compactMeta}>
            <Text style={[styles.compactBranch, { color: branchColor }]}>
              {config.label}
            </Text>
            <Text style={[styles.compactTime, { color: neutral.textMuted }]}>
              {dayjs(item.published_at).fromNow()}
            </Text>
          </View>
        </View>
        {onSave && (
          <Pressable style={styles.saveButton} onPress={() => onSave(item)} hitSlop={8}>
            <Ionicons
              name={isSaved ? 'bookmark' : 'bookmark-outline'}
              size={20}
              color={isSaved ? branchColors.agency : neutral.textMuted}
            />
          </Pressable>
        )}
      </Pressable>
    );
  }

  return (
    <Pressable
      style={[styles.container, { backgroundColor: neutral.card }]}
      onPress={() => onPress?.(item)}
    >
      {/* Left color bar */}
      <View style={[styles.colorBar, { backgroundColor: branchColor }]} />

      <View style={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.branchInfo}>
            <Ionicons name={config.icon} size={14} color={branchColor} />
            <Text style={[styles.branchLabel, { color: branchColor }]}>
              {config.label.toUpperCase()}
            </Text>
          </View>
          <Text style={[styles.time, { color: neutral.textMuted }]}>
            {dayjs(item.published_at).fromNow()}
          </Text>
        </View>

        {/* Headline */}
        <Text style={[styles.headline, { color: neutral.textPrimary }]} numberOfLines={2}>
          {item.headline}
        </Text>

        {/* Summary */}
        <Text style={[styles.summary, { color: neutral.textSecondary }]} numberOfLines={2}>
          {item.summary}
        </Text>

        {/* Footer */}
        <View style={styles.footer}>
          <View style={styles.tagsContainer}>
            {item.tags.slice(0, 2).map(tag => (
              <View key={tag} style={[styles.tag, { backgroundColor: neutral.surface }]}>
                <Text style={[styles.tagText, { color: neutral.textSecondary }]}>{tag}</Text>
              </View>
            ))}
          </View>

          {onSave && (
            <Pressable style={styles.saveButton} onPress={() => onSave(item)} hitSlop={8}>
              <Ionicons
                name={isSaved ? 'bookmark' : 'bookmark-outline'}
                size={20}
                color={isSaved ? branchColors.agency : neutral.textMuted}
              />
            </Pressable>
          )}
        </View>
      </View>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    borderRadius: 16,
    marginBottom: 12,
    overflow: 'hidden',
  },
  colorBar: {
    width: 4,
  },
  content: {
    flex: 1,
    padding: 16,
    gap: 10,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  branchInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  branchLabel: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  time: {
    fontSize: 12,
  },
  headline: {
    fontSize: 17,
    fontWeight: '600',
    lineHeight: 22,
  },
  summary: {
    fontSize: 14,
    lineHeight: 20,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  tagsContainer: {
    flexDirection: 'row',
    gap: 8,
    flex: 1,
  },
  tag: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '500',
  },
  saveButton: {
    padding: 4,
  },
  // Compact styles
  compactContainer: {
    flexDirection: 'row',
    borderRadius: 12,
    marginBottom: 8,
    overflow: 'hidden',
  },
  compactBar: {
    width: 3,
  },
  compactContent: {
    flex: 1,
    padding: 12,
    gap: 6,
  },
  compactHeadline: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 20,
  },
  compactMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  compactBranch: {
    fontSize: 11,
    fontWeight: '600',
  },
  compactTime: {
    fontSize: 11,
  },
});

export default UpdateCard;
