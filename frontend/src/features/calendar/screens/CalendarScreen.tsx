import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { StyleSheet, Text, View, Pressable, ScrollView, Dimensions, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import dayjs from 'dayjs';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { RootStackParamList } from '@navigation/RootNavigator';
import { fetchUpdates, GovernmentUpdate } from '@services/updatesService';
import { FeedItem } from '@features/feed/types';
import YearView from './YearView';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarScreen = () => {
  const { neutral, branch: branchColors } = useTheme();
  const navigation = useNavigation<NavigationProp>();

  const [currentDate, setCurrentDate] = useState(dayjs());
  const [selectedDate, setSelectedDate] = useState(dayjs());
  const [updates, setUpdates] = useState<GovernmentUpdate[]>([]);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'month' | 'year'>('month');

  const startOfMonth = currentDate.startOf('month');
  const endOfMonth = currentDate.endOf('month');
  const startDayOfWeek = startOfMonth.day(); // 0-6
  const daysInMonth = currentDate.daysInMonth();

  // Fetch updates when month/year changes
  useEffect(() => {
    const loadUpdates = async () => {
      setLoading(true);
      let start, end;

      if (viewMode === 'month') {
        start = startOfMonth.toISOString();
        end = endOfMonth.toISOString();
      } else {
        start = currentDate.startOf('year').toISOString();
        end = currentDate.endOf('year').toISOString();
      }

      const data = await fetchUpdates(start, end, 500);
      setUpdates(data);
      setLoading(false);
    };
    loadUpdates();
  }, [currentDate, viewMode]);

  // Generate calendar grid
  const calendarDays = useMemo(() => {
    const days = [];
    // Padding for previous month
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null);
    }
    // Actual days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(startOfMonth.date(i));
    }
    return days;
  }, [currentDate]);

  // Group updates by date for the calendar dots
  const updatesByDate = useMemo(() => {
    const map: Record<string, { hasCongress: boolean; hasExecutive: boolean; hasJudicial: boolean }> = {};
    updates.forEach(u => {
      const dateKey = dayjs(u.published_at).format('YYYY-MM-DD');
      if (!map[dateKey]) {
        map[dateKey] = { hasCongress: false, hasExecutive: false, hasJudicial: false };
      }
      if (u.branch === 'legislative') map[dateKey].hasCongress = true;
      if (u.branch === 'executive') map[dateKey].hasExecutive = true;
      if (u.branch === 'judicial') map[dateKey].hasJudicial = true;
    });
    return map;
  }, [updates]);

  // Filter updates for the selected day
  const selectedDayUpdates = useMemo(() => {
    return updates.filter(u => dayjs(u.published_at).isSame(selectedDate, 'day'));
  }, [updates, selectedDate]);

  // Convert GovernmentUpdate to FeedItem for navigation
  const convertToFeedItem = useCallback((update: GovernmentUpdate): FeedItem => ({
    id: update.id,
    headline: update.headline,
    summary: update.summary || '',
    published_at: update.published_at,
    branch: update.branch as FeedItem['branch'],
    source: update.source,
    url: update.url,
    tags: update.tags || [],
    metadata: update.metadata,
  }), []);

  const handleUpdatePress = useCallback((update: GovernmentUpdate) => {
    navigation.navigate('UpdateDetail', { item: convertToFeedItem(update) });
  }, [navigation, convertToFeedItem]);

  const renderDay = (date: dayjs.Dayjs | null, index: number) => {
    if (!date) {
      return <View key={`empty-${index}`} style={styles.dayCell} />;
    }

    const dateKey = date.format('YYYY-MM-DD');
    const activity = updatesByDate[dateKey] || { hasCongress: false, hasExecutive: false, hasJudicial: false };
    const isSelected = date.isSame(selectedDate, 'day');
    const isToday = date.isSame(dayjs(), 'day');

    return (
      <Pressable
        key={dateKey}
        style={[
          styles.dayCell,
          isSelected && [styles.selectedDayCell, { borderColor: branchColors.agency }],
          isToday && !isSelected && styles.todayCell
        ]}
        onPress={() => setSelectedDate(date)}
      >
        <Text style={[
          styles.dayText,
          { color: neutral.textPrimary },
          isSelected && [styles.selectedDayText, { color: branchColors.agency }],
          isToday && !isSelected && styles.todayText
        ]}>
          {date.date()}
        </Text>
        <View style={styles.dotContainer}>
          {activity.hasCongress && <View style={[styles.dot, { backgroundColor: branchColors.legislative }]} />}
          {activity.hasExecutive && <View style={[styles.dot, { backgroundColor: branchColors.executive }]} />}
          {activity.hasJudicial && <View style={[styles.dot, { backgroundColor: branchColors.judicial }]} />}
        </View>
      </Pressable>
    );
  };

  const getBranchColor = (branch: string) => {
    return branchColors[branch as keyof typeof branchColors] || neutral.textMuted;
  };

  return (
    <LinearGradient colors={[neutral.surface, neutral.background]} style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.navContainer}>
          <Pressable
            onPress={() => setCurrentDate(viewMode === 'month' ? currentDate.subtract(1, 'month') : currentDate.subtract(1, 'year'))}
            style={styles.navButton}
          >
            <Ionicons name="chevron-back" size={24} color={neutral.textMuted} />
          </Pressable>
          <Text style={[styles.monthTitle, { color: neutral.textPrimary }]}>
            {viewMode === 'month' ? currentDate.format('MMMM YYYY') : currentDate.format('YYYY')}
          </Text>
          <Pressable
            onPress={() => setCurrentDate(viewMode === 'month' ? currentDate.add(1, 'month') : currentDate.add(1, 'year'))}
            style={styles.navButton}
          >
            <Ionicons name="chevron-forward" size={24} color={neutral.textMuted} />
          </Pressable>
        </View>

        <Pressable
          style={[styles.viewToggle, { backgroundColor: neutral.card }]}
          onPress={() => setViewMode(viewMode === 'month' ? 'year' : 'month')}
        >
          <Ionicons
            name={viewMode === 'month' ? 'grid' : 'calendar'}
            size={16}
            color={neutral.textMuted}
          />
          <Text style={[styles.viewToggleText, { color: neutral.textMuted }]}>
            {viewMode === 'month' ? 'Year' : 'Month'}
          </Text>
        </Pressable>
      </View>

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: branchColors.legislative }]} />
          <Text style={[styles.legendText, { color: neutral.textMuted }]}>Congress</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: branchColors.executive }]} />
          <Text style={[styles.legendText, { color: neutral.textMuted }]}>Executive</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: branchColors.judicial }]} />
          <Text style={[styles.legendText, { color: neutral.textMuted }]}>Judicial</Text>
        </View>
      </View>

      {viewMode === 'month' ? (
        <>
          {/* Weekday Headers */}
          <View style={styles.weekRow}>
            {DAYS_OF_WEEK.map(day => (
              <Text key={day} style={[styles.weekDayText, { color: neutral.textMuted }]}>{day}</Text>
            ))}
          </View>

          {/* Calendar Grid */}
          <View style={styles.calendarGrid}>
            {loading ? (
              <ActivityIndicator size="large" color={branchColors.agency} style={{ margin: 20 }} />
            ) : (
              calendarDays.map((date, index) => renderDay(date, index))
            )}
          </View>

          {/* Selected Day Summary */}
          <View style={[styles.summaryContainer, { backgroundColor: neutral.card }]}>
            <View style={styles.summaryHeader}>
              <Text style={[styles.summaryTitle, { color: neutral.textPrimary }]}>
                {selectedDate.format('MMM D, YYYY')}
              </Text>
              <Text style={[styles.summaryCount, { color: neutral.textMuted }]}>
                {selectedDayUpdates.length} update{selectedDayUpdates.length !== 1 ? 's' : ''}
              </Text>
            </View>
            <ScrollView style={styles.feed} showsVerticalScrollIndicator={false}>
              {selectedDayUpdates.length > 0 ? (
                selectedDayUpdates.map(update => (
                  <Pressable
                    key={update.id}
                    style={[styles.card, { backgroundColor: neutral.surface }]}
                    onPress={() => handleUpdatePress(update)}
                  >
                    <View style={[styles.cardBar, { backgroundColor: getBranchColor(update.branch) }]} />
                    <View style={styles.cardContent}>
                      <View style={styles.cardHeader}>
                        <Text style={[styles.cardTag, { color: getBranchColor(update.branch) }]}>
                          {update.branch.toUpperCase()}
                        </Text>
                        <Text style={[styles.cardTime, { color: neutral.textMuted }]}>
                          {dayjs(update.published_at).format('h:mm A')}
                        </Text>
                      </View>
                      <Text style={[styles.cardHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                        {update.headline}
                      </Text>
                      {update.summary && (
                        <Text style={[styles.cardSummary, { color: neutral.textSecondary }]} numberOfLines={2}>
                          {update.summary}
                        </Text>
                      )}
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={neutral.textMuted} />
                  </Pressable>
                ))
              ) : (
                <View style={styles.emptyContainer}>
                  <Ionicons name="calendar-outline" size={32} color={neutral.textMuted} />
                  <Text style={[styles.emptyState, { color: neutral.textMuted }]}>
                    No activity recorded for this date.
                  </Text>
                </View>
              )}
            </ScrollView>
          </View>
        </>
      ) : (
        <YearView
          year={currentDate.year()}
          updates={updates}
          onMonthSelect={(month) => {
            setCurrentDate(currentDate.month(month));
            setSelectedDate(currentDate.month(month));
            setViewMode('month');
          }}
        />
      )}
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  navContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  navButton: {
    padding: 8,
  },
  viewToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 16,
    gap: 6,
  },
  viewToggleText: {
    fontSize: 14,
    fontWeight: '600',
  },
  monthTitle: {
    fontSize: 20,
    fontWeight: '700',
    marginHorizontal: 8,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 16,
    marginBottom: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontSize: 12,
    fontWeight: '500',
  },
  weekRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 10,
  },
  weekDayText: {
    fontSize: 12,
    fontWeight: '600',
    width: 40,
    textAlign: 'center',
  },
  calendarGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
  },
  dayCell: {
    width: (Dimensions.get('window').width - 32) / 7,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 5,
    borderRadius: 8,
  },
  selectedDayCell: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderWidth: 1,
  },
  todayCell: {
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
  },
  dayText: {
    fontSize: 16,
  },
  selectedDayText: {
    fontWeight: '700',
  },
  todayText: {
    fontWeight: '600',
  },
  dotContainer: {
    flexDirection: 'row',
    gap: 2,
    marginTop: 4,
  },
  dot: {
    width: 4,
    height: 4,
    borderRadius: 2,
  },
  summaryContainer: {
    flex: 1,
    marginTop: 16,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
    marginHorizontal: -16,
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
  },
  summaryCount: {
    fontSize: 14,
  },
  feed: {
    flex: 1,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    borderRadius: 12,
    marginBottom: 10,
    overflow: 'hidden',
  },
  cardBar: {
    width: 4,
    alignSelf: 'stretch',
  },
  cardContent: {
    flex: 1,
    padding: 14,
    gap: 6,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  cardTag: {
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  cardTime: {
    fontSize: 11,
  },
  cardHeadline: {
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
  },
  cardSummary: {
    fontSize: 13,
    lineHeight: 18,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 40,
    gap: 12,
  },
  emptyState: {
    fontSize: 14,
    textAlign: 'center',
  },
});

export default CalendarScreen;
