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
  }
});

export default DailyBriefScreen;
