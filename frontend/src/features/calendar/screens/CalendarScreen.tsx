import React, { useState, useMemo, useEffect } from 'react';
import { StyleSheet, Text, View, Pressable, ScrollView, Dimensions, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import dayjs from 'dayjs';
import { useTheme } from '@theme/ThemeProvider';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { RootStackParamList } from '@navigation/RootNavigator';
import { fetchUpdates, GovernmentUpdate } from '@services/updatesService';
import YearView from './YearView';

type Props = NativeStackScreenProps<RootStackParamList, 'Calendar'>;

const DAYS_OF_WEEK = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarScreen = ({ navigation }: Props) => {
  const { neutral, branch } = useTheme();
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
          isSelected && styles.selectedDayCell,
          isToday && !isSelected && styles.todayCell
        ]}
        onPress={() => setSelectedDate(date)}
      >
        <Text style={[
          styles.dayText,
          isSelected && styles.selectedDayText,
          isToday && !isSelected && styles.todayText
        ]}>
          {date.date()}
        </Text>
        <View style={styles.dotContainer}>
          {activity.hasCongress && <View style={[styles.dot, { backgroundColor: '#EF4444' }]} />}
          {activity.hasExecutive && <View style={[styles.dot, { backgroundColor: '#3B82F6' }]} />}
          {activity.hasJudicial && <View style={[styles.dot, { backgroundColor: '#EAB308' }]} />}
        </View>
      </Pressable>
    );
  };

  const getBranchColor = (branch: string) => {
    switch (branch) {
      case 'legislative': return '#EF4444';
      case 'executive': return '#3B82F6';
      case 'judicial': return '#EAB308';
      default: return '#94A3B8';
    }
  };

  return (
    <LinearGradient colors={['#0F172A', '#020617']} style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.navContainer}>
          <Pressable onPress={() => setCurrentDate(viewMode === 'month' ? currentDate.subtract(1, 'month') : currentDate.subtract(1, 'year'))}>
            <Text style={styles.navArrow}>{'<'}</Text>
          </Pressable>
          <Text style={styles.monthTitle}>
            {viewMode === 'month' ? currentDate.format('MMMM YYYY') : currentDate.format('YYYY')}
          </Text>
          <Pressable onPress={() => setCurrentDate(viewMode === 'month' ? currentDate.add(1, 'month') : currentDate.add(1, 'year'))}>
            <Text style={styles.navArrow}>{'>'}</Text>
          </Pressable>
        </View>

        <Pressable
          style={styles.viewToggle}
          onPress={() => setViewMode(viewMode === 'month' ? 'year' : 'month')}
        >
          <Text style={styles.viewToggleText}>{viewMode === 'month' ? 'Year' : 'Month'}</Text>
        </Pressable>
      </View>

      {viewMode === 'month' ? (
        <>
          {/* Weekday Headers */}
          <View style={styles.weekRow}>
            {DAYS_OF_WEEK.map(day => (
              <Text key={day} style={styles.weekDayText}>{day}</Text>
            ))}
          </View>

          {/* Calendar Grid */}
          <View style={styles.calendarGrid}>
            {loading ? (
              <ActivityIndicator size="large" color="#F59E0B" style={{ margin: 20 }} />
            ) : (
              calendarDays.map((date, index) => renderDay(date, index))
            )}
          </View>

          {/* Selected Day Summary */}
          <View style={styles.summaryContainer}>
            <Text style={styles.summaryTitle}>
              Updates for {selectedDate.format('MMM D, YYYY')}
            </Text>
            <ScrollView style={styles.feed}>
              {selectedDayUpdates.length > 0 ? (
                selectedDayUpdates.map(update => (
                  <View key={update.id} style={[styles.card, { borderLeftColor: getBranchColor(update.branch) }]}>
                    <Text style={styles.cardTag}>{update.branch}</Text>
                    <Text style={styles.cardHeadline}>{update.headline}</Text>
                    {update.summary ? (
                      <Text style={styles.cardSummary} numberOfLines={3}>
                        {update.summary}
                      </Text>
                    ) : null}
                  </View>
                ))
              ) : (
                <Text style={styles.emptyState}>No activity recorded for this date.</Text>
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
            setSelectedDate(currentDate.month(month)); // Also update selectedDate to the first day of the selected month
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
    marginBottom: 20,
  },
  navContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  viewToggle: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  viewToggleText: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '600',
  },
  monthTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#F8FAFC',
    marginHorizontal: 10,
  },
  navArrow: {
    fontSize: 24,
    color: '#94A3B8',
    padding: 10,
  },
  weekRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 10,
  },
  weekDayText: {
    color: '#64748B',
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
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    borderWidth: 1,
    borderColor: '#F59E0B',
  },
  todayCell: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
  },
  dayText: {
    color: '#E2E8F0',
    fontSize: 16,
  },
  selectedDayText: {
    color: '#F59E0B',
    fontWeight: '700',
  },
  todayText: {
    color: '#F8FAFC',
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
    marginTop: 20,
    backgroundColor: 'rgba(15, 23, 42, 0.6)',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 20,
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#F8FAFC',
    marginBottom: 16,
  },
  feed: {
    flex: 1,
  },
  card: {
    backgroundColor: 'rgba(30, 41, 59, 0.5)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
  },
  cardTag: {
    color: '#94A3B8',
    fontSize: 12,
    textTransform: 'uppercase',
    fontWeight: '700',
    marginBottom: 4,
  },
  cardHeadline: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 8,
  },
  cardSummary: {
    color: '#CBD5F5',
    fontSize: 14,
    lineHeight: 20,
  },
  emptyState: {
    color: '#64748B',
    fontStyle: 'italic',
    textAlign: 'center',
    marginTop: 20,
  },
});

export default CalendarScreen;
