import React, { useCallback } from 'react';
import {
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useSavedItems } from '../../../context/SavedItemsContext';
import { useUserPreferences } from '../../../context/UserPreferencesContext';
import { FeedItem } from '@features/feed/types';
import { RootStackParamList } from '@navigation/RootNavigator';
import dayjs from '@utils/dayjs';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const interestLabels: Record<string, string> = {
  legislative: 'Congress',
  judicial: 'Courts',
  executive: 'Executive',
  budget: 'Budget',
  oversight: 'Oversight',
};

const YouScreen = () => {
  const { neutral, branch: branchColors, semantic, spacing } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const { savedItems, clearAll } = useSavedItems();
  const {
    preferences,
    setNotificationPreferences,
    resetOnboarding,
  } = useUserPreferences();

  const handleItemPress = useCallback((item: FeedItem) => {
    navigation.navigate('UpdateDetail', { item });
  }, [navigation]);

  const handleEditInterests = useCallback(() => {
    navigation.navigate('Onboarding');
  }, [navigation]);

  const handleNotificationSettings = useCallback(() => {
    navigation.navigate('NotificationSettings');
  }, [navigation]);

  const handleClearSaved = useCallback(() => {
    Alert.alert(
      'Clear All Saved Items',
      'Are you sure you want to remove all saved items? This cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Clear All', style: 'destructive', onPress: clearAll },
      ]
    );
  }, [clearAll]);

  const followingCount = {
    bills: preferences.followedBills.length,
    members: preferences.followedMembers.length,
    topics: preferences.followedTopics.length,
  };
  const districtLabel = preferences.homeDistrict?.state && preferences.homeDistrict?.district
    ? `${preferences.homeDistrict.state}-${preferences.homeDistrict.district}`
    : null;
  const representative = preferences.currentMembers.find(member => member.chamber === 'House');
  const senators = preferences.currentMembers.filter(member => member.chamber === 'Senate');

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.headerTitle, { color: neutral.textPrimary }]}>
          Your Briefing
        </Text>
      </View>

      {/* Following Summary */}
      <View style={[styles.section, { backgroundColor: neutral.card }]}>
        <View style={styles.sectionHeader}>
          <Ionicons name="bookmark" size={20} color={branchColors.agency} />
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
            Following
          </Text>
        </View>
        <View style={styles.followingRow}>
          <View style={styles.followingStat}>
            <Text style={[styles.followingNumber, { color: branchColors.legislative }]}>
              {followingCount.bills}
            </Text>
            <Text style={[styles.followingLabel, { color: neutral.textMuted }]}>Bills</Text>
          </View>
          <View style={[styles.followingDivider, { backgroundColor: neutral.divider }]} />
          <View style={styles.followingStat}>
            <Text style={[styles.followingNumber, { color: branchColors.executive }]}>
              {followingCount.members}
            </Text>
            <Text style={[styles.followingLabel, { color: neutral.textMuted }]}>Members</Text>
          </View>
          <View style={[styles.followingDivider, { backgroundColor: neutral.divider }]} />
          <View style={styles.followingStat}>
            <Text style={[styles.followingNumber, { color: branchColors.judicial }]}>
              {followingCount.topics}
            </Text>
            <Text style={[styles.followingLabel, { color: neutral.textMuted }]}>Topics</Text>
          </View>
        </View>
      </View>

      {/* My Government */}
      <View style={[styles.section, { backgroundColor: neutral.card }]}>
        <View style={styles.sectionHeader}>
          <Ionicons name="business" size={20} color={branchColors.legislative} />
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
            My Government
          </Text>
          {districtLabel && (
            <Text style={[styles.districtBadge, { color: branchColors.legislative, backgroundColor: neutral.surface }]}>
              {districtLabel}
            </Text>
          )}
        </View>

        {!preferences.homeDistrict ? (
          <View style={styles.emptyState}>
            <Ionicons name="location-outline" size={32} color={neutral.textMuted} />
            <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
              Add a district lookup to show your representative and senators here.
            </Text>
          </View>
        ) : (
          <View style={styles.memberList}>
            {preferences.districtLookupAmbiguity && (
              <Text style={[styles.lookupWarning, { color: semantic.warning }]}>
                {preferences.districtLookupAmbiguity}
              </Text>
            )}
            {representative && (
              <View style={[styles.memberRow, { borderBottomColor: neutral.divider }]}>
                <View style={styles.memberInfo}>
                  <Text style={[styles.memberRole, { color: neutral.textMuted }]}>Representative</Text>
                  <Text style={[styles.memberName, { color: neutral.textPrimary }]}>
                    {representative.name}
                  </Text>
                </View>
                <Text style={[styles.memberParty, { color: neutral.textMuted }]}>
                  {representative.party ?? ''}
                </Text>
              </View>
            )}
            {senators.map(senator => (
              <View key={senator.bioguide_id} style={[styles.memberRow, { borderBottomColor: neutral.divider }]}>
                <View style={styles.memberInfo}>
                  <Text style={[styles.memberRole, { color: neutral.textMuted }]}>Senator</Text>
                  <Text style={[styles.memberName, { color: neutral.textPrimary }]}>
                    {senator.name}
                  </Text>
                </View>
                <Text style={[styles.memberParty, { color: neutral.textMuted }]}>
                  {senator.party ?? ''}
                </Text>
              </View>
            ))}
            {preferences.currentMembers.length === 0 && (
              <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
                No current members are loaded for this district yet.
              </Text>
            )}
          </View>
        )}
      </View>

      {/* Saved Items */}
      <View style={[styles.section, { backgroundColor: neutral.card }]}>
        <View style={styles.sectionHeader}>
          <Ionicons name="star" size={20} color={branchColors.agency} />
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
            Saved Items
          </Text>
          {savedItems.length > 0 && (
            <Pressable onPress={handleClearSaved} style={styles.clearButton}>
              <Text style={[styles.clearButtonText, { color: semantic.error }]}>Clear All</Text>
            </Pressable>
          )}
        </View>

        {savedItems.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="bookmark-outline" size={32} color={neutral.textMuted} />
            <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
              No saved items yet. Tap the bookmark icon on any update to save it here.
            </Text>
          </View>
        ) : (
          <View style={styles.savedList}>
            {savedItems.slice(0, 5).map(item => (
              <Pressable
                key={item.id}
                style={[styles.savedItem, { borderBottomColor: neutral.divider }]}
                onPress={() => handleItemPress(item)}
              >
                <View style={[styles.savedItemBar, { backgroundColor: branchColors[item.branch] || branchColors.legislative }]} />
                <View style={styles.savedItemContent}>
                  <Text style={[styles.savedItemHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                    {item.headline}
                  </Text>
                  <Text style={[styles.savedItemMeta, { color: neutral.textMuted }]}>
                    {item.branch.toUpperCase()} • {dayjs(item.published_at).fromNow()}
                  </Text>
                </View>
                <Ionicons name="chevron-forward" size={20} color={neutral.textMuted} />
              </Pressable>
            ))}
            {savedItems.length > 5 && (
              <Text style={[styles.moreItemsText, { color: neutral.textMuted }]}>
                +{savedItems.length - 5} more items
              </Text>
            )}
          </View>
        )}
      </View>

      {/* Notifications */}
      <View style={[styles.section, { backgroundColor: neutral.card }]}>
        <View style={styles.sectionHeader}>
          <Ionicons name="notifications" size={20} color={branchColors.agency} />
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
            Notifications
          </Text>
        </View>

        <View style={styles.settingsList}>
          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>Daily Digest</Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                {preferences.notifications.dailyDigestTime}
              </Text>
            </View>
            <Switch
              value={preferences.notifications.dailyDigest}
              onValueChange={(value) => setNotificationPreferences({ dailyDigest: value })}
              trackColor={{ false: neutral.divider, true: branchColors.agency + '80' }}
              thumbColor={preferences.notifications.dailyDigest ? branchColors.agency : neutral.textMuted}
            />
          </View>

          <View style={[styles.settingRow, { borderBottomColor: neutral.divider }]}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>Breaking News</Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Urgent government updates
              </Text>
            </View>
            <Switch
              value={preferences.notifications.breakingNews}
              onValueChange={(value) => setNotificationPreferences({ breakingNews: value })}
              trackColor={{ false: neutral.divider, true: branchColors.agency + '80' }}
              thumbColor={preferences.notifications.breakingNews ? branchColors.agency : neutral.textMuted}
            />
          </View>

          <View style={styles.settingRow}>
            <View style={styles.settingInfo}>
              <Text style={[styles.settingLabel, { color: neutral.textPrimary }]}>Bill Updates</Text>
              <Text style={[styles.settingDescription, { color: neutral.textMuted }]}>
                Updates on followed bills
              </Text>
            </View>
            <Switch
              value={preferences.notifications.billUpdates}
              onValueChange={(value) => setNotificationPreferences({ billUpdates: value })}
              trackColor={{ false: neutral.divider, true: branchColors.agency + '80' }}
              thumbColor={preferences.notifications.billUpdates ? branchColors.agency : neutral.textMuted}
            />
          </View>
        </View>

        <Pressable
          style={[styles.settingsLink, { borderTopColor: neutral.divider }]}
          onPress={handleNotificationSettings}
        >
          <Text style={[styles.settingsLinkText, { color: branchColors.agency }]}>
            More notification settings
          </Text>
          <Ionicons name="chevron-forward" size={20} color={branchColors.agency} />
        </Pressable>
      </View>

      {/* Interests */}
      <View style={[styles.section, { backgroundColor: neutral.card }]}>
        <View style={styles.sectionHeader}>
          <Ionicons name="heart" size={20} color={branchColors.agency} />
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>
            Interests
          </Text>
        </View>

        <View style={styles.interestsList}>
          {preferences.interests.length === 0 ? (
            <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>
              No interests selected yet.
            </Text>
          ) : (
            <View style={styles.interestChips}>
              {preferences.interests.map(interest => (
                <View
                  key={interest}
                  style={[styles.interestChip, { backgroundColor: neutral.surface }]}
                >
                  <Text style={[styles.interestChipText, { color: neutral.textPrimary }]}>
                    {interestLabels[interest] || interest}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>

        <Pressable
          style={[styles.settingsLink, { borderTopColor: neutral.divider }]}
          onPress={handleEditInterests}
        >
          <Text style={[styles.settingsLinkText, { color: branchColors.agency }]}>
            Edit your interests
          </Text>
          <Ionicons name="chevron-forward" size={20} color={branchColors.agency} />
        </Pressable>
      </View>

      {/* App Info */}
      <View style={styles.footer}>
        <Text style={[styles.footerText, { color: neutral.textMuted }]}>
          Congresscape v0.1.0
        </Text>
        <Text style={[styles.footerText, { color: neutral.textMuted }]}>
          Your daily briefing on federal government activity
        </Text>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 60,
    paddingHorizontal: 16,
    paddingBottom: 100,
    gap: 16,
  },
  header: {
    paddingVertical: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '800',
  },
  section: {
    borderRadius: 20,
    padding: 16,
    gap: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
  },
  clearButton: {
    padding: 4,
  },
  clearButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  followingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-around',
    paddingVertical: 8,
  },
  followingStat: {
    alignItems: 'center',
    gap: 4,
    flex: 1,
  },
  followingNumber: {
    fontSize: 28,
    fontWeight: '700',
  },
  followingLabel: {
    fontSize: 12,
    fontWeight: '500',
  },
  followingDivider: {
    width: 1,
    height: 40,
  },
  districtBadge: {
    fontSize: 13,
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  memberList: {
    gap: 0,
  },
  memberRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 10,
    borderBottomWidth: 1,
    gap: 12,
  },
  memberInfo: {
    flex: 1,
    gap: 2,
  },
  memberRole: {
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  memberName: {
    fontSize: 15,
    fontWeight: '600',
  },
  memberParty: {
    fontSize: 13,
    fontWeight: '500',
  },
  lookupWarning: {
    fontSize: 13,
    lineHeight: 18,
  },
  emptyState: {
    alignItems: 'center',
    gap: 12,
    paddingVertical: 20,
  },
  emptyText: {
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  savedList: {
    gap: 0,
  },
  savedItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    gap: 12,
  },
  savedItemBar: {
    width: 3,
    height: 40,
    borderRadius: 2,
  },
  savedItemContent: {
    flex: 1,
    gap: 4,
  },
  savedItemHeadline: {
    fontSize: 15,
    fontWeight: '500',
    lineHeight: 20,
  },
  savedItemMeta: {
    fontSize: 12,
  },
  moreItemsText: {
    fontSize: 14,
    textAlign: 'center',
    paddingTop: 12,
  },
  settingsList: {
    gap: 0,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
  },
  settingInfo: {
    flex: 1,
    gap: 2,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '500',
  },
  settingDescription: {
    fontSize: 13,
  },
  settingsLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
  },
  settingsLinkText: {
    fontSize: 15,
    fontWeight: '500',
  },
  interestsList: {
    gap: 8,
  },
  interestChips: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  interestChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
  interestChipText: {
    fontSize: 14,
    fontWeight: '500',
  },
  footer: {
    alignItems: 'center',
    gap: 4,
    paddingVertical: 20,
  },
  footerText: {
    fontSize: 12,
  },
});

export default YouScreen;
