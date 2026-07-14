import React, { ReactNode, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

import { useTheme } from '@theme/ThemeProvider';

type Props = {
  title: string;
  summary?: string | null;
  defaultOpen?: boolean;
  children: ReactNode;
};

const DisclosureSection = ({ title, summary, defaultOpen = false, children }: Props) => {
  const { neutral } = useTheme();
  const [open, setOpen] = useState(defaultOpen);

  return (
    <View style={[styles.section, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
      <Pressable
        style={styles.header}
        onPress={() => setOpen(value => !value)}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
      >
        <View style={styles.headerText}>
          <Text style={[styles.title, { color: neutral.textMuted }]}>{title.toUpperCase()}</Text>
          {summary ? (
            <Text style={[styles.summary, { color: neutral.textSecondary }]} numberOfLines={open ? 2 : 1}>
              {summary}
            </Text>
          ) : null}
        </View>
        <Ionicons
          name={open ? 'chevron-up' : 'chevron-down'}
          size={18}
          color={neutral.textMuted}
        />
      </Pressable>
      {open ? <View style={[styles.body, { borderTopColor: neutral.divider }]}>{children}</View> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  section: {
    borderWidth: 1,
    borderRadius: 8,
  },
  header: {
    minHeight: 52,
    paddingHorizontal: 12,
    paddingVertical: 10,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
  },
  headerText: {
    flex: 1,
    gap: 3,
  },
  title: {
    fontSize: 12,
    fontWeight: '800',
  },
  summary: {
    fontSize: 13,
    lineHeight: 18,
  },
  body: {
    borderTopWidth: StyleSheet.hairlineWidth,
    padding: 12,
    gap: 10,
  },
});

export default DisclosureSection;
