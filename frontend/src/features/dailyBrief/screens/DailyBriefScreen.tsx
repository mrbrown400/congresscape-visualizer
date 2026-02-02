import React, { useMemo } from 'react';
import { ActivityIndicator, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';

import FeedCard from '@features/feed/components/FeedCard';
import { useDailyBrief } from '../hooks/useDailyBrief';
import { useTheme } from '@theme/ThemeProvider';

const DailyBriefScreen = () => {
  const { neutral } = useTheme();
  const { brief, loading, error, reload } = useDailyBrief();

  const content = useMemo(() => {
    if (loading && !brief) {
      return (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color="#F59E0B" />
          <Text style={styles.loaderText}>Preparing today&apos;s briefing…</Text>
        </View>
      );
    }

    if (error) {
      return <Text style={styles.errorText}>{error}</Text>;
    }

    if (!brief) {
      return <Text style={styles.emptyText}>No government actions to report yet today.</Text>;
    }

    return (
      <View style={styles.contentWrapper}>
        <View style={styles.header}>
          <Text style={styles.kicker}>Daily Briefing</Text>
          <Text style={styles.headline}>{brief.headline}</Text>
          <Text style={styles.narrative}>{brief.narrative}</Text>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Highlights</Text>
          {brief.highlights.map(highlight => (
            <View key={`${highlight.headline}-${highlight.published_at}`} style={styles.highlightCard}>
              <Text style={styles.highlightHeadline}>{highlight.headline}</Text>
              {!!highlight.summary && <Text style={styles.highlightSummary}>{highlight.summary}</Text>}
              <View style={styles.highlightMeta}>
                <Text style={styles.highlightChip}>{highlight.branch.toUpperCase()}</Text>
                <Text style={styles.highlightTimestamp}>
                  {new Date(highlight.published_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {brief.upcoming_events && brief.upcoming_events.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Coming Up</Text>
            {brief.upcoming_events.slice(0, 5).map(event => (
              <View key={`${event.headline}-${event.event_date}`} style={styles.upcomingCard}>
                <View style={styles.upcomingDateBadge}>
                  <Text style={styles.upcomingDateText}>
                    {new Date(event.event_date).toLocaleDateString([], { month: 'short', day: 'numeric' })}
                  </Text>
                </View>
                <View style={styles.upcomingContent}>
                  <Text style={styles.upcomingHeadline} numberOfLines={2}>{event.headline}</Text>
                  <View style={styles.upcomingMeta}>
                    <Text style={styles.upcomingChip}>{event.branch.toUpperCase()}</Text>
                    <Text style={styles.upcomingType}>{event.event_type.replace('_', ' ')}</Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Deep dives</Text>
          {brief.top_updates.map(update => (
            <FeedCard key={update.id} item={update} />
          ))}
        </View>
      </View>
    );
  }, [brief, error, loading]);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={<RefreshControl refreshing={loading} onRefresh={reload} tintColor="#F59E0B" />}
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
    paddingBottom: 120
  },
  loader: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    paddingTop: 120
  },
  loaderText: {
    color: '#F8FAFC',
    fontSize: 16
  },
  errorText: {
    color: '#FECACA',
    textAlign: 'center',
    marginTop: 120
  },
  emptyText: {
    color: '#C7D2FE',
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
    color: '#FBBF24',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 1.5,
    textTransform: 'uppercase'
  },
  headline: {
    color: '#F8FAFC',
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 30
  },
  narrative: {
    color: '#E2E8F0',
    fontSize: 16,
    lineHeight: 22
  },
  section: {
    gap: 16
  },
  sectionTitle: {
    color: '#E0F2FE',
    fontSize: 18,
    fontWeight: '700'
  },
  highlightCard: {
    backgroundColor: 'rgba(15, 33, 60, 0.8)',
    borderRadius: 20,
    padding: 16,
    gap: 8
  },
  highlightHeadline: {
    color: '#F8FAFC',
    fontSize: 16,
    fontWeight: '600'
  },
  highlightSummary: {
    color: '#E2E8F0',
    fontSize: 14,
    lineHeight: 20
  },
  highlightMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  highlightChip: {
    color: '#0B1D3A',
    backgroundColor: '#F8FAFC',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    fontSize: 12,
    fontWeight: '700'
  },
  highlightTimestamp: {
    color: '#C7D2FE',
    fontSize: 12
  },
  upcomingCard: {
    backgroundColor: 'rgba(15, 33, 60, 0.6)',
    borderRadius: 16,
    padding: 12,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'center'
  },
  upcomingDateBadge: {
    backgroundColor: '#F59E0B',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 8,
    minWidth: 56,
    alignItems: 'center'
  },
  upcomingDateText: {
    color: '#0B1D3A',
    fontSize: 12,
    fontWeight: '700',
    textAlign: 'center'
  },
  upcomingContent: {
    flex: 1,
    gap: 6
  },
  upcomingHeadline: {
    color: '#F8FAFC',
    fontSize: 14,
    fontWeight: '600'
  },
  upcomingMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8
  },
  upcomingChip: {
    color: '#0B1D3A',
    backgroundColor: '#10B981',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    fontSize: 10,
    fontWeight: '700'
  },
  upcomingType: {
    color: '#94A3B8',
    fontSize: 12,
    textTransform: 'capitalize'
  }
});

export default DailyBriefScreen;
