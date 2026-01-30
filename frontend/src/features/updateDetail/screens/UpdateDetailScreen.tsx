import React, { useMemo } from 'react';
import {
  Linking,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useSavedItems } from '../../../context/SavedItemsContext';
import { RootStackParamList } from '@navigation/RootNavigator';
import { Branch } from '@features/feed/types';
import dayjs from '@utils/dayjs';
import BillStatusTracker from '../components/BillStatusTracker';

type Props = NativeStackScreenProps<RootStackParamList, 'UpdateDetail'>;

const branchConfig: Record<string, { icon: keyof typeof Ionicons.glyphMap; label: string }> = {
  legislative: { icon: 'business', label: 'Legislative' },
  house: { icon: 'business', label: 'House' },
  senate: { icon: 'business', label: 'Senate' },
  executive: { icon: 'document-text', label: 'Executive' },
  judicial: { icon: 'scale', label: 'Judicial' },
  agency: { icon: 'grid', label: 'Agency' },
};

const UpdateDetailScreen = ({ route, navigation }: Props) => {
  const { item } = route.params;
  const { neutral, branch: branchColors, semantic, spacing } = useTheme();
  const { isSaved, toggleSave } = useSavedItems();

  const branchColor = branchColors[item.branch as Branch] || branchColors.legislative;
  const config = branchConfig[item.branch] || branchConfig.legislative;
  const saved = isSaved(item.id);

  // Determine if this is a bill (for showing status tracker)
  const isBill = useMemo(() => {
    const lowerHeadline = item.headline.toLowerCase();
    const lowerTags = item.tags.map(t => t.toLowerCase());
    return (
      lowerHeadline.includes('bill') ||
      lowerHeadline.includes('h.r.') ||
      lowerHeadline.includes('s.') ||
      lowerHeadline.includes('act') ||
      lowerTags.includes('bill') ||
      lowerTags.includes('legislation')
    );
  }, [item]);

  // Extract bill status from metadata if available
  const billStatus = useMemo(() => {
    if (!isBill) return null;

    // Default to introduced status, can be enhanced with real data
    const status = (item.metadata?.status as string) || 'introduced';
    const statusMap: Record<string, number> = {
      'introduced': 0,
      'committee': 1,
      'floor': 2,
      'passed_house': 2,
      'passed_senate': 2,
      'other_chamber': 3,
      'conference': 4,
      'president': 5,
      'signed': 6,
      'vetoed': 6,
    };
    return statusMap[status] ?? 0;
  }, [isBill, item.metadata]);

  const handleShare = async () => {
    try {
      await Share.share({
        message: `${item.headline}\n\n${item.summary}${item.url ? `\n\nRead more: ${item.url}` : ''}`,
        title: item.headline,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const handleOpenUrl = () => {
    if (item.url) {
      Linking.openURL(item.url);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      {/* Header */}
      <View style={[styles.header, { borderBottomColor: neutral.divider }]}>
        <Pressable
          style={styles.backButton}
          onPress={() => navigation.goBack()}
          hitSlop={12}
        >
          <Ionicons name="arrow-back" size={24} color={neutral.textPrimary} />
        </Pressable>
        <View style={styles.headerActions}>
          <Pressable
            style={styles.headerButton}
            onPress={() => toggleSave(item)}
            hitSlop={8}
          >
            <Ionicons
              name={saved ? 'bookmark' : 'bookmark-outline'}
              size={24}
              color={saved ? branchColors.agency : neutral.textPrimary}
            />
          </Pressable>
          <Pressable
            style={styles.headerButton}
            onPress={handleShare}
            hitSlop={8}
          >
            <Ionicons name="share-outline" size={24} color={neutral.textPrimary} />
          </Pressable>
        </View>
      </View>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Branch Badge */}
        <View style={styles.branchRow}>
          <View style={[styles.branchBadge, { backgroundColor: branchColor + '20' }]}>
            <Ionicons name={config.icon} size={16} color={branchColor} />
            <Text style={[styles.branchText, { color: branchColor }]}>
              {config.label.toUpperCase()}
            </Text>
          </View>
        </View>

        {/* Main Content */}
        <Text style={[styles.headline, { color: neutral.textPrimary }]}>
          {item.headline}
        </Text>

        <View style={styles.metaRow}>
          <Text style={[styles.source, { color: neutral.textMuted }]}>
            {item.source.toUpperCase()}
          </Text>
          <Text style={[styles.metaDot, { color: neutral.textMuted }]}>•</Text>
          <Text style={[styles.date, { color: neutral.textMuted }]}>
            {dayjs(item.published_at).format('MMM D, YYYY h:mm A')}
          </Text>
        </View>

        {/* Bill Status Tracker */}
        {isBill && billStatus !== null && (
          <View style={styles.statusSection}>
            <Text style={[styles.sectionLabel, { color: neutral.textMuted }]}>STATUS</Text>
            <BillStatusTracker currentStep={billStatus} />
          </View>
        )}

        {/* Summary */}
        <View style={styles.summarySection}>
          <Text style={[styles.sectionLabel, { color: neutral.textMuted }]}>SUMMARY</Text>
          <Text style={[styles.summary, { color: neutral.textSecondary }]}>
            {item.summary}
          </Text>
        </View>

        {/* Tags */}
        {item.tags.length > 0 && (
          <View style={styles.tagsSection}>
            <Text style={[styles.sectionLabel, { color: neutral.textMuted }]}>TOPICS</Text>
            <View style={styles.tagsContainer}>
              {item.tags.map(tag => (
                <View
                  key={tag}
                  style={[styles.tag, { backgroundColor: neutral.card }]}
                >
                  <Text style={[styles.tagText, { color: neutral.textPrimary }]}>{tag}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Timeline (Placeholder for future enhancement) */}
        <View style={styles.timelineSection}>
          <Text style={[styles.sectionLabel, { color: neutral.textMuted }]}>TIMELINE</Text>
          <View style={[styles.timelineItem, { borderLeftColor: branchColor }]}>
            <Text style={[styles.timelineDate, { color: neutral.textMuted }]}>
              {dayjs(item.published_at).format('MMM D')}
            </Text>
            <Text style={[styles.timelineEvent, { color: neutral.textPrimary }]}>
              Published
            </Text>
          </View>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionsSection}>
          {item.url && (
            <Pressable
              style={[styles.primaryButton, { backgroundColor: branchColor }]}
              onPress={handleOpenUrl}
            >
              <Ionicons name="open-outline" size={20} color="#FFFFFF" />
              <Text style={styles.primaryButtonText}>View Full Text</Text>
            </Pressable>
          )}

          <Pressable
            style={[styles.secondaryButton, { borderColor: branchColor }]}
            onPress={() => toggleSave(item)}
          >
            <Ionicons
              name={saved ? 'bookmark' : 'bookmark-outline'}
              size={20}
              color={branchColor}
            />
            <Text style={[styles.secondaryButtonText, { color: branchColor }]}>
              {saved ? 'Saved' : 'Track This Update'}
            </Text>
          </Pressable>
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 100,
    gap: 20,
  },
  branchRow: {
    flexDirection: 'row',
  },
  branchBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  branchText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  headline: {
    fontSize: 26,
    fontWeight: '800',
    lineHeight: 34,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  source: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 0.5,
  },
  metaDot: {
    fontSize: 12,
  },
  date: {
    fontSize: 12,
  },
  statusSection: {
    gap: 12,
  },
  sectionLabel: {
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 1.5,
  },
  summarySection: {
    gap: 12,
  },
  summary: {
    fontSize: 16,
    lineHeight: 26,
  },
  tagsSection: {
    gap: 12,
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  tagText: {
    fontSize: 14,
    fontWeight: '500',
  },
  timelineSection: {
    gap: 12,
  },
  timelineItem: {
    paddingLeft: 16,
    borderLeftWidth: 3,
    gap: 4,
  },
  timelineDate: {
    fontSize: 12,
    fontWeight: '600',
  },
  timelineEvent: {
    fontSize: 15,
    fontWeight: '500',
  },
  actionsSection: {
    gap: 12,
    paddingTop: 8,
  },
  primaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
    gap: 8,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderRadius: 16,
    borderWidth: 2,
    gap: 8,
  },
  secondaryButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});

export default UpdateDetailScreen;
