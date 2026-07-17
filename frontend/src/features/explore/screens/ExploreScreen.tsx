import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useFeed } from '@features/feed/hooks/useFeed';
import { FeedItem } from '@features/feed/types';
import { useSavedItems } from '../../../context/SavedItemsContext';
import FeedCard from '@features/feed/components/FeedCard';
import { RootStackParamList } from '@navigation/RootNavigator';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

type FilterKey = 'all' | 'city' | 'county' | 'metro' | 'federal';
type QuickFilter = 'meetings' | 'actions';

const scopeFilters: { key: FilterKey; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'all', label: 'All local', icon: 'apps' },
  { key: 'city', label: 'City', icon: 'business' },
  { key: 'county', label: 'County', icon: 'map' },
  { key: 'metro', label: 'Metro', icon: 'train' },
  { key: 'federal', label: 'Federal', icon: 'flag' },
];

const quickFilters: { key: QuickFilter; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'meetings', label: 'Meetings', icon: 'calendar' },
  { key: 'actions', label: 'Actions', icon: 'checkmark-circle' },
];

const trendingTopics = [
  'Housing',
  'Transit',
  'Public safety',
  'Budget and contracts',
  'Climate resilience',
];

const ExploreScreen = () => {
  const { neutral, branch: branchColors } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const { isSaved, toggleSave } = useSavedItems();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeScope, setActiveScope] = useState<FilterKey>('all');
  const [activeQuickFilter, setActiveQuickFilter] = useState<QuickFilter | null>(null);

  const contextKey = useMemo(() => {
    if (activeQuickFilter) return activeQuickFilter;
    return activeScope;
  }, [activeQuickFilter, activeScope]);

  const { items, loading, reload } = useFeed(contextKey);

  // Filter items based on search
  const filteredItems = useMemo(() => {
    if (!searchQuery.trim()) return items;

    const query = searchQuery.toLowerCase();
    return items.filter(item =>
      item.headline.toLowerCase().includes(query) ||
      (item.summary ?? '').toLowerCase().includes(query) ||
      item.tags.some(tag => tag.toLowerCase().includes(query))
    );
  }, [items, searchQuery]);

  const handleItemPress = useCallback((item: FeedItem) => {
    navigation.navigate('UpdateDetail', { item });
  }, [navigation]);

  const handleScopeSelect = (key: FilterKey) => {
    setActiveScope(key);
    setActiveQuickFilter(null);
  };

  const handleQuickFilterSelect = (key: QuickFilter) => {
    setActiveQuickFilter(activeQuickFilter === key ? null : key);
    setActiveScope('all');
  };

  const handleTopicPress = (topic: string) => {
    setSearchQuery(topic);
  };

  const renderItem = useCallback(({ item }: { item: FeedItem }) => (
    <FeedCard
      item={item}
      onPress={handleItemPress}
      onSave={toggleSave}
      isSaved={isSaved(item.id)}
    />
  ), [handleItemPress, toggleSave, isSaved]);

  const ListHeader = (
    <View style={styles.headerContainer}>
      <View style={styles.pageHeader}>
        <Text style={[styles.pageTitle, { color: neutral.textPrimary }]}>Explore</Text>
        <Text style={[styles.pageSubtitle, { color: neutral.textSecondary }]}>
          Search City, County, Metro, and federal records with their official source trails.
        </Text>
      </View>

      {/* Search Bar */}
      <View style={[styles.searchContainer, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
        <Ionicons name="search" size={20} color={neutral.textMuted} />
        <TextInput
          style={[styles.searchInput, { color: neutral.textPrimary }]}
          placeholder="Search agencies, projects, meetings, topics..."
          placeholderTextColor={neutral.textMuted}
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="none"
          autoCorrect={false}
        />
        {searchQuery.length > 0 && (
          <Pressable onPress={() => setSearchQuery('')}>
            <Ionicons name="close-circle" size={20} color={neutral.textMuted} />
          </Pressable>
        )}
      </View>

      {/* Jurisdiction Filters */}
      <View style={styles.filterSection}>
        <Text style={[styles.filterLabel, { color: neutral.textMuted }]}>JURISDICTION</Text>
        <View style={styles.filterRow}>
          {scopeFilters.map(filter => {
            const isActive = activeScope === filter.key;
            const color = branchColors.legislative;

            return (
              <Pressable
                key={filter.key}
                style={[
                  styles.filterChip,
                  {
                    backgroundColor: isActive ? color : neutral.card,
                    borderColor: isActive ? color : neutral.border,
                  }
                ]}
                onPress={() => handleScopeSelect(filter.key)}
              >
                <Ionicons
                  name={filter.icon}
                  size={16}
                  color={isActive ? '#FFFFFF' : neutral.textSecondary}
                />
                <Text style={[
                  styles.filterChipText,
                  { color: isActive ? '#FFFFFF' : neutral.textSecondary }
                ]}>
                  {filter.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Quick Filters */}
      <View style={styles.filterSection}>
        <Text style={[styles.filterLabel, { color: neutral.textMuted }]}>QUICK FILTERS</Text>
        <View style={styles.filterRow}>
          {quickFilters.map(filter => {
            const isActive = activeQuickFilter === filter.key;
            const color = branchColors.legislative;

            return (
              <Pressable
                key={filter.key}
                style={[
                  styles.filterChip,
                  {
                    backgroundColor: isActive ? color : neutral.card,
                    borderColor: isActive ? color : neutral.border,
                  }
                ]}
                onPress={() => handleQuickFilterSelect(filter.key)}
              >
                <Ionicons
                  name={filter.icon}
                  size={16}
                  color={isActive ? '#FFFFFF' : neutral.textSecondary}
                />
                <Text style={[
                  styles.filterChipText,
                  { color: isActive ? '#FFFFFF' : neutral.textSecondary }
                ]}>
                  {filter.label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      {/* Trending Topics (only shown when no search) */}
      {!searchQuery && (
        <View style={styles.filterSection}>
          <Text style={[styles.filterLabel, { color: neutral.textMuted }]}>TRENDING TOPICS</Text>
          <View style={styles.topicsContainer}>
            {trendingTopics.map(topic => (
              <Pressable
                key={topic}
                style={[styles.topicChip, { backgroundColor: neutral.card, borderColor: neutral.divider }]}
                onPress={() => handleTopicPress(topic)}
              >
                <Ionicons name="pricetag-outline" size={14} color={branchColors.legislative} />
                <Text style={[styles.topicText, { color: neutral.textPrimary }]}>{topic}</Text>
              </Pressable>
            ))}
          </View>
        </View>
      )}

      {/* Results Header */}
      <View style={styles.resultsHeader}>
        <Text style={[styles.resultsLabel, { color: neutral.textMuted }]}>
          {searchQuery ? `RESULTS FOR "${searchQuery.toUpperCase()}"` : 'LATEST UPDATES'}
        </Text>
        <Text style={[styles.resultsCount, { color: neutral.textMuted }]}>
          {filteredItems.length} items
        </Text>
      </View>
    </View>
  );

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      <FlatList
        data={filteredItems}
        keyExtractor={item => item.id.toString()}
        renderItem={renderItem}
        ListHeaderComponent={ListHeader}
        contentContainerStyle={styles.listContent}
        refreshing={loading}
        onRefresh={reload}
        ListEmptyComponent={
          loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={branchColors.legislative} />
            </View>
          ) : (
            <View style={styles.emptyContainer}>
              <Ionicons name="search-outline" size={48} color={neutral.textMuted} />
              <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
                {searchQuery ? 'No results found' : 'No updates available'}
              </Text>
            </View>
          )
        }
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  listContent: {
    paddingTop: 60,
    paddingHorizontal: 16,
    paddingBottom: 100,
    width: '100%',
    maxWidth: 1040,
    alignSelf: 'center',
  },
  headerContainer: {
    gap: 18,
    marginBottom: 20,
  },
  pageHeader: {
    gap: 6,
  },
  pageTitle: {
    fontSize: 32,
    lineHeight: 38,
    fontWeight: '800',
  },
  pageSubtitle: {
    fontSize: 15,
    lineHeight: 21,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderRadius: 8,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
  },
  filterSection: {
    gap: 10,
  },
  filterLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    gap: 6,
  },
  filterChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  topicsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  topicChip: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    gap: 6,
  },
  topicText: {
    fontSize: 14,
    fontWeight: '500',
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 8,
  },
  resultsLabel: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0,
  },
  resultsCount: {
    fontSize: 12,
  },
  loadingContainer: {
    paddingVertical: 40,
    alignItems: 'center',
  },
  emptyContainer: {
    paddingVertical: 60,
    alignItems: 'center',
    gap: 12,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
  },
});

export default ExploreScreen;
