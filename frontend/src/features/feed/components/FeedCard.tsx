import React from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@theme/ThemeProvider';
import dayjs from '@utils/dayjs';
import { FeedItem } from '../types';

type Props = {
  item: FeedItem;
  onPress?: (item: FeedItem) => void;
  onSave?: (item: FeedItem) => void;
};

const FeedCard = ({ item, onPress, onSave }: Props) => {
  const { branch, neutral } = useTheme();
  const accent = branch[item.branch] ?? branch.legislative;

  return (
    <Pressable onPress={() => onPress?.(item)} style={styles.cardContainer}>
      <LinearGradient colors={[accent, neutral.card]} style={styles.cardBackground}>
        <View style={styles.headerRow}>
          <View style={[styles.badge, { backgroundColor: accent }]}>
            <Text style={styles.badgeText}>{item.branch.toUpperCase()}</Text>
          </View>
          <Text style={styles.timeText}>{dayjs(item.published_at).fromNow()}</Text>
        </View>

        <Text style={styles.headline}>{item.headline}</Text>
        <Text style={styles.summary} numberOfLines={3}>
          {item.summary}
        </Text>

        <View style={styles.footerRow}>
          <Text style={styles.source}>{item.source.toUpperCase()}</Text>
          <View style={styles.tagRow}>
            {item.tags.slice(0, 2).map(tag => (
              <View key={tag} style={styles.tagChip}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      </LinearGradient>
    </Pressable>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    marginBottom: 16
  },
  cardBackground: {
    borderRadius: 24,
    padding: 20,
    gap: 12
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  badge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 999
  },
  badgeText: {
    color: '#F8FAFC',
    fontSize: 12,
    fontWeight: '700'
  },
  timeText: {
    color: '#C7D2FE',
    fontSize: 12
  },
  headline: {
    color: '#F8FAFC',
    fontSize: 18,
    fontWeight: '700'
  },
  summary: {
    color: '#E2E8F0',
    fontSize: 14,
    lineHeight: 20
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  source: {
    color: '#C7D2FE',
    fontSize: 12,
    letterSpacing: 1
  },
  tagRow: {
    flexDirection: 'row',
    gap: 8
  },
  tagChip: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999
  },
  tagText: {
    color: '#E0F2FE',
    fontSize: 12
  }
});

export default FeedCard;
