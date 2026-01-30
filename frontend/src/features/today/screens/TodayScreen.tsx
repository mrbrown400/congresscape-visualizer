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

import { useDailyBrief } from '@features/dailyBrief/hooks/useDailyBrief';
import { useTheme } from '@theme/ThemeProvider';
import { useSavedItems } from '../../../context/SavedItemsContext';
import { FeedItem, Branch } from '@features/feed/types';
import dayjs from '@utils/dayjs';
import { RootStackParamList } from '@navigation/RootNavigator';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const branchConfig: Record<string, { icon: keyof typeof Ionicons.glyphMap; label: string }> = {
  legislative: { icon: 'business', label: 'Legislative' },
  house: { icon: 'business', label: 'House' },
  senate: { icon: 'business', label: 'Senate' },
  executive: { icon: 'document-text', label: 'Executive' },
  judicial: { icon: 'scale', label: 'Judicial' },
  agency: { icon: 'grid', label: 'Agency' },
};

const TodayScreen = () => {
  const { neutral, branch: branchColors, semantic, typography, spacing } = useTheme();
  const { brief, loading, error, reload } = useDailyBrief();
  const { isSaved, toggleSave } = useSavedItems();
  const navigation = useNavigation<NavigationProp>();

  const handleItemPress = useCallback((item: FeedItem) => {
    navigation.navigate('UpdateDetail', { item });
  }, [navigation]);

  const groupedUpdates = useMemo(() => {
    if (!brief?.top_updates) return {};

    const groups: Record<string, FeedItem[]> = {};
    brief.top_updates.forEach(item => {
      const branch = item.branch || 'legislative';
      if (!groups[branch]) {
        groups[branch] = [];
      }
      groups[branch].push(item);
    });
    return groups;
  }, [brief]);

  const urgentItems = useMemo(() => {
    if (!brief?.highlights) return [];
    return brief.highlights.filter(h =>
      h.tags?.includes('urgent') || h.tags?.includes('breaking')
    );
  }, [brief]);

  const content = useMemo(() => {
    if (loading && !brief) {
      return (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color={branchColors.agency} />
          <Text style={[styles.loaderText, { color: neutral.textPrimary }]}>
            Preparing today's briefing...
          </Text>
        </View>
      );
    }

    if (error) {
      return (
        <View style={styles.errorContainer}>
          <Ionicons name="cloud-offline" size={48} color={semantic.error} />
          <Text style={[styles.errorText, { color: semantic.error }]}>{error}</Text>
          <Pressable style={[styles.retryButton, { backgroundColor: branchColors.agency }]} onPress={reload}>
            <Text style={styles.retryText}>Try Again</Text>
          </Pressable>
        </View>
      );
    }

    if (!brief) {
      return (
        <View style={styles.emptyContainer}>
          <Ionicons name="newspaper-outline" size={48} color={neutral.textMuted} />
          <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
            No government actions to report yet today.
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.contentWrapper}>
        {/* Date Header */}
        <View style={styles.dateHeader}>
          <Ionicons name="sunny" size={24} color={branchColors.agency} />
          <Text style={[styles.dateText, { color: neutral.textPrimary }]}>
            {dayjs().format('dddd, MMMM D').toUpperCase()}
          </Text>
        </View>

        {/* Hero Headline Card */}
        <View style={[styles.heroCard, { backgroundColor: neutral.card }]}>
          <View style={styles.heroLabel}>
            <Ionicons name="newspaper" size={16} color={branchColors.agency} />
            <Text style={[styles.heroLabelText, { color: branchColors.agency }]}>
              TODAY'S HEADLINE
            </Text>
          </View>
          <Text style={[styles.heroHeadline, { color: neutral.textPrimary }]}>
            {brief.headline}
          </Text>
          <Text style={[styles.heroNarrative, { color: neutral.textSecondary }]}>
            {brief.narrative}
          </Text>
        </View>

        {/* Urgent Section */}
        {urgentItems.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionTitleRow}>
                <Ionicons name="alert-circle" size={20} color={semantic.urgent} />
                <Text style={[styles.sectionTitle, { color: semantic.urgent }]}>URGENT</Text>
              </View>
            </View>
            {urgentItems.map((item, idx) => (
              <Pressable
                key={`urgent-${idx}`}
                style={[styles.urgentCard, { backgroundColor: neutral.card, borderLeftColor: semantic.urgent }]}
              >
                <View style={styles.urgentDot} />
                <Text style={[styles.urgentText, { color: neutral.textPrimary }]}>
                  {item.headline}
                </Text>
              </Pressable>
            ))}
          </View>
        )}

        {/* By Branch Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={[styles.sectionDivider, { color: neutral.textMuted }]}>BY BRANCH</Text>
          </View>

          {Object.entries(groupedUpdates).map(([branchKey, items]) => {
            const config = branchConfig[branchKey] || branchConfig.legislative;
            const color = branchColors[branchKey as Branch] || branchColors.legislative;

            return (
              <View key={branchKey} style={styles.branchSection}>
                <View style={styles.branchHeader}>
                  <View style={[styles.branchIconContainer, { backgroundColor: color + '20' }]}>
                    <Ionicons name={config.icon} size={20} color={color} />
                  </View>
                  <Text style={[styles.branchLabel, { color: neutral.textPrimary }]}>
                    {config.label}
                  </Text>
                  <View style={styles.branchCount}>
                    <Text style={[styles.branchCountText, { color: neutral.textMuted }]}>
                      {items.length} update{items.length !== 1 ? 's' : ''}
                    </Text>
                    <Ionicons name="chevron-forward" size={16} color={neutral.textMuted} />
                  </View>
                </View>

                {items.slice(0, 3).map(item => (
                  <Pressable
                    key={item.id}
                    style={[styles.updateItem, { borderLeftColor: color }]}
                    onPress={() => handleItemPress(item)}
                  >
                    <View style={styles.updateContent}>
                      <Text style={[styles.updateHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                        {item.headline}
                      </Text>
                      <Text style={[styles.updateTime, { color: neutral.textMuted }]}>
                        {dayjs(item.published_at).fromNow()}
                      </Text>
                    </View>
                    <Pressable
                      style={styles.saveButton}
                      onPress={() => toggleSave(item)}
                      hitSlop={8}
                    >
                      <Ionicons
                        name={isSaved(item.id) ? 'bookmark' : 'bookmark-outline'}
                        size={20}
                        color={isSaved(item.id) ? branchColors.agency : neutral.textMuted}
                      />
                    </Pressable>
                  </Pressable>
                ))}
              </View>
            );
          })}
        </View>

        {/* Highlights Section */}
        {brief.highlights.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={[styles.sectionDivider, { color: neutral.textMuted }]}>HIGHLIGHTS</Text>
            </View>

            {brief.highlights.filter(h => !urgentItems.includes(h)).slice(0, 5).map((highlight, idx) => {
              const color = branchColors[highlight.branch as Branch] || branchColors.legislative;
              return (
                <View
                  key={`highlight-${idx}`}
                  style={[styles.highlightCard, { backgroundColor: neutral.card }]}
                >
                  <View style={[styles.highlightBranchBar, { backgroundColor: color }]} />
                  <View style={styles.highlightContent}>
                    <View style={styles.highlightHeader}>
                      <Text style={[styles.highlightBranch, { color }]}>
                        {highlight.branch.toUpperCase()}
                      </Text>
                      <Text style={[styles.highlightTime, { color: neutral.textMuted }]}>
                        {dayjs(highlight.published_at).format('h:mm A')}
                      </Text>
                    </View>
                    <Text style={[styles.highlightHeadline, { color: neutral.textPrimary }]}>
                      {highlight.headline}
                    </Text>
                    {highlight.summary && (
                      <Text style={[styles.highlightSummary, { color: neutral.textSecondary }]} numberOfLines={2}>
                        {highlight.summary}
                      </Text>
                    )}
                  </View>
                </View>
              );
            })}
          </View>
        )}
      </View>
    );
  }, [brief, error, loading, groupedUpdates, urgentItems, branchColors, neutral, semantic, isSaved, toggleSave, handleItemPress, reload]);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={
        <RefreshControl
          refreshing={loading}
          onRefresh={reload}
          tintColor={branchColors.agency}
        />
      }
    >
      {content}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingTop: 60,
    paddingBottom: 100,
  },
  loader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingTop: 120,
  },
  loaderText: {
    fontSize: 16,
  },
  errorContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
    paddingTop: 120,
  },
  errorText: {
    fontSize: 16,
    textAlign: 'center',
  },
  retryButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 999,
  },
  retryText: {
    color: '#0B1D3A',
    fontSize: 14,
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingTop: 120,
  },
  emptyText: {
    fontSize: 16,
    textAlign: 'center',
  },
  contentWrapper: {
    gap: 24,
  },
  dateHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dateText: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 1,
  },
  heroCard: {
    borderRadius: 20,
    padding: 20,
    gap: 12,
  },
  heroLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  heroLabelText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 1,
  },
  heroHeadline: {
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 30,
  },
  heroNarrative: {
    fontSize: 16,
    lineHeight: 24,
  },
  section: {
    gap: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  sectionTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  sectionDivider: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1.5,
  },
  urgentCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    gap: 12,
  },
  urgentDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#EF4444',
  },
  urgentText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
  },
  branchSection: {
    gap: 8,
  },
  branchHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingVertical: 8,
  },
  branchIconContainer: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  branchLabel: {
    fontSize: 16,
    fontWeight: '600',
    flex: 1,
  },
  branchCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  branchCountText: {
    fontSize: 14,
  },
  updateItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingLeft: 16,
    paddingVertical: 12,
    marginLeft: 18,
    borderLeftWidth: 2,
    gap: 12,
  },
  updateContent: {
    flex: 1,
    gap: 4,
  },
  updateHeadline: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 20,
  },
  updateTime: {
    fontSize: 12,
  },
  saveButton: {
    padding: 4,
  },
  highlightCard: {
    flexDirection: 'row',
    borderRadius: 16,
    overflow: 'hidden',
  },
  highlightBranchBar: {
    width: 4,
  },
  highlightContent: {
    flex: 1,
    padding: 16,
    gap: 8,
  },
  highlightHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  highlightBranch: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  highlightTime: {
    fontSize: 12,
  },
  highlightHeadline: {
    fontSize: 16,
    fontWeight: '600',
    lineHeight: 22,
  },
  highlightSummary: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default TodayScreen;
