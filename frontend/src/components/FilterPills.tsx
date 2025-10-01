import React from 'react';
import { Pressable, ScrollView, StyleSheet, Text } from 'react-native';

import { defaultFilters } from '@constants/filters';

type Props = {
  active: string;
  onChange: (key: string) => void;
};

const FilterPills = ({ active, onChange }: Props) => (
  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.container}>
    {defaultFilters.map(filter => {
      const isActive = filter.key === active;
      return (
        <Pressable
          key={filter.key}
          onPress={() => onChange(filter.key)}
          style={[styles.pill, isActive && styles.activePill]}
        >
          <Text style={[styles.label, isActive && styles.activeLabel]}>{filter.label}</Text>
        </Pressable>
      );
    })}
  </ScrollView>
);

const styles = StyleSheet.create({
  container: {
    gap: 12,
    paddingVertical: 8
  },
  pill: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.1)'
  },
  activePill: {
    backgroundColor: '#F59E0B'
  },
  label: {
    color: '#E0F2FE',
    fontWeight: '500'
  },
  activeLabel: {
    color: '#0B1D3A'
  }
});

export default FilterPills;
