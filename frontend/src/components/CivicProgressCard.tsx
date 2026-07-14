import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@theme/ThemeProvider';

export type CivicProgressItem = {
  label: string;
  detail: string;
  complete: boolean;
};

type Props = {
  title: string;
  subtitle: string;
  items: CivicProgressItem[];
};

const CivicProgressCard = ({ title, subtitle, items }: Props) => {
  const { neutral, branch } = useTheme();
  const completed = items.filter(item => item.complete).length;
  const ratio = items.length > 0 ? completed / items.length : 0;

  return (
    <View style={[styles.card, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
      <View style={styles.header}>
        <View style={styles.headerText}>
          <Text style={[styles.title, { color: neutral.textPrimary }]}>{title}</Text>
          <Text style={[styles.subtitle, { color: neutral.textSecondary }]}>{subtitle}</Text>
        </View>
        <Text style={[styles.count, { color: branch.legislative }]}>
          {completed}/{items.length}
        </Text>
      </View>

      <View style={[styles.track, { backgroundColor: neutral.background }]}>
        <View style={[styles.bar, { backgroundColor: branch.legislative, width: `${ratio * 100}%` }]} />
      </View>

      <View style={styles.itemList}>
        {items.map(item => (
          <View key={item.label} style={styles.itemRow}>
            <Ionicons
              name={item.complete ? 'checkmark-circle' : 'ellipse-outline'}
              size={17}
              color={item.complete ? branch.legislative : neutral.textMuted}
            />
            <View style={styles.itemText}>
              <Text style={[styles.itemLabel, { color: neutral.textPrimary }]}>{item.label}</Text>
              <Text style={[styles.itemDetail, { color: neutral.textMuted }]}>{item.detail}</Text>
            </View>
          </View>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 14,
    gap: 12,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerText: {
    flex: 1,
    gap: 4,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
  },
  subtitle: {
    fontSize: 13,
    lineHeight: 18,
  },
  count: {
    fontSize: 18,
    fontWeight: '800',
  },
  track: {
    height: 6,
    borderRadius: 3,
    overflow: 'hidden',
  },
  bar: {
    height: 6,
    borderRadius: 3,
  },
  itemList: {
    gap: 9,
  },
  itemRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  itemText: {
    flex: 1,
    gap: 1,
  },
  itemLabel: {
    fontSize: 13,
    fontWeight: '800',
  },
  itemDetail: {
    fontSize: 12,
    lineHeight: 16,
  },
});

export default CivicProgressCard;
