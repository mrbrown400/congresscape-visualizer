import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { defaultFilters } from '@constants/filters';
import { useTheme } from '@theme/ThemeProvider';

type Props = {
  active: string;
  onChange: (key: string) => void;
};

const FilterPills = ({ active, onChange }: Props) => {
  const { neutral, branch } = useTheme();

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.container}>
      {defaultFilters.map(filter => {
        const isActive = filter.key === active;
        return (
          <Pressable
            key={filter.key}
            onPress={() => onChange(filter.key)}
            style={[
              styles.pill,
              {
                backgroundColor: isActive ? branch.legislative : neutral.card,
                borderColor: isActive ? branch.legislative : neutral.divider,
              },
            ]}
          >
            <Text style={[styles.label, { color: isActive ? '#FFFFFF' : neutral.textSecondary }]}>
              {filter.label}
            </Text>
          </Pressable>
        );
      })}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    paddingVertical: 8
  },
  pill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
  label: {
    fontWeight: '700',
  }
});

export default FilterPills;
