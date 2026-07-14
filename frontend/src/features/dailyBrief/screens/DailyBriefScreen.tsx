import React, { useMemo } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import FeedCard from '@features/feed/components/FeedCard';
import { useDailyBrief } from '../hooks/useDailyBrief';
import { useTheme } from '@theme/ThemeProvider';

const DailyBriefScreen = () => {
  const { neutral, branch } = useTheme();
  const { brief, loading, error, reload } = useDailyBrief();

  const content = useMemo(() => {
    if (loading && !brief) {
      return (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color={branch.legislative} />
          <Text style={[styles.loaderText, { color: neutral.textSecondary }]}>
            Preparing today's briefing...
          </Text>
        </View>
      );
    }

    if (error) {
      return <Text style={[styles.errorText, { color: '#B91C1C' }]}>{error}</Text>;
    }

    if (!brief) {
      return (
        <Text style={[styles.emptyText, { color: neutral.textMuted }]}>
          No government actions to report yet today.
        </Text>
      );
    }

    return (
      <View style={styles.contentWrapper}>
        <View style={styles.header}>
          <Text style={[styles.kicker, { color: branch.legislative }]}>Daily Briefing</Text>
          <Text style={[styles.headline, { color: neutral.textPrimary }]}>{brief.headline}</Text>
          <Text style={[styles.narrative, { color: neutral.textSecondary }]}>{brief.narrative}</Text>
        </View>

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Highlights</Text>
          {brief.highlights.map(highlight => (
            <View
              key={`${highlight.headline}-${highlight.published_at}`}
              style={[styles.highlightCard, { backgroundColor: neutral.card, borderColor: neutral.divider }]}
            >
              <Text style={[styles.highlightHeadline, { color: neutral.textPrimary }]}>
                {highlight.headline}
              </Text>
              {!!highlight.summary && (
                <Text style={[styles.highlightSummary, { color: neutral.textSecondary }]}>
                  {highlight.summary}
                </Text>
              )}
              <View style={styles.highlightMeta}>
                <Text style={[styles.highlightChip, { color: branch.legislative, borderColor: neutral.divider }]}>
                  {highlight.branch.toUpperCase()}
                </Text>
                <Text style={[styles.highlightTimestamp, { color: neutral.textMuted }]}>
                  {new Date(highlight.published_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {brief.upcoming_events && brief.upcoming_events.length > 0 && (
          <View style={styles.section}>
            <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Coming Up</Text>
            {brief.upcoming_events.slice(0, 5).map(event => (
              <View
                key={`${event.headline}-${event.event_date}`}
                style={[styles.upcomingCard, { backgroundColor: neutral.card, borderColor: neutral.divider }]}
              >
                <View style={[styles.upcomingDateBadge, { backgroundColor: branch.legislative }]}>
                  <Text style={styles.upcomingDateText}>
                    {new Date(event.event_date).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                  </Text>
                </View>
                <View style={styles.upcomingContent}>
                  <Text style={[styles.upcomingHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                    {event.headline}
                  </Text>
                  <View style={styles.upcomingMeta}>
                    <Text style={[styles.upcomingChip, { color: branch.executive, borderColor: neutral.divider }]}>
                      {event.branch.toUpperCase()}
                    </Text>
                    <Text style={[styles.upcomingType, { color: neutral.textMuted }]}>
                      {event.event_type.replace('_', ' ')}
                    </Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Deep dives</Text>
          {brief.top_updates.map(update => (
            <FeedCard key={update.id} item={update} />
          ))}
        </View>
      </View>
    );
  }, [brief, branch, error, loading, neutral]);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={reload} tintColor={branch.legislative} />}
    >
      {content}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 120,
    width: '100%',
    maxWidth: 1040,
    alignSelf: 'center',
  },
  loader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingTop: 120
  },
  loaderText: {
    fontSize: 16
  },
  errorText: {
    textAlign: 'center',
    marginTop: 120
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 120
  },
  contentWrapper: {
    gap: 28
  },
  header: {
    gap: 12
  },
  kicker: {
    fontSize: 14,
    fontWeight: '800',
    letterSpacing: 0,
    textTransform: 'uppercase'
  },
  headline: {
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 30
  },
  narrative: {
    fontSize: 16,
    lineHeight: 22
  },
  section: {
    gap: 16
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800'
  },
  highlightCard: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    gap: 8
  },
  highlightHeadline: {
    fontSize: 16,
    fontWeight: '800'
  },
  highlightSummary: {
    fontSize: 14,
    lineHeight: 20
  },
  highlightMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  highlightChip: {
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    fontSize: 12,
    fontWeight: '800'
  },
  highlightTimestamp: {
    fontSize: 12
  },
  upcomingCard: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center'
  },
  upcomingDateBadge: {
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    minWidth: 56,
    alignItems: 'center'
  },
  upcomingDateText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center'
  },
  upcomingContent: {
    flex: 1,
    gap: 6
  },
  upcomingHeadline: {
    fontSize: 14,
    fontWeight: '800'
  },
  upcomingMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8
  },
  upcomingChip: {
    borderWidth: 1,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    fontSize: 10,
    fontWeight: '800'
  },
  upcomingType: {
    fontSize: 12,
    textTransform: 'capitalize'
  }
});

export default DailyBriefScreen;
