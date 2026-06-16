import React, { useCallback, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useFeed } from '@features/feed/hooks/useFeed';
import { FeedItem } from '@features/feed/types';
import { CurrentMember } from '@features/members/types';
import { useDistrictLookup } from '@features/members/hooks/useDistrictLookup';
import { useUserPreferences } from '@context/UserPreferencesContext';
import { RootStackParamList } from '@navigation/RootNavigator';
import { useTheme } from '@theme/ThemeProvider';
import dayjs from '@utils/dayjs';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const defaultTopics = ['budget', 'oversight', 'health', 'technology', 'veterans'];

const YouScreen = () => {
  const { neutral, branch: branchColors, semantic } = useTheme();
  const navigation = useNavigation<NavigationProp>();
  const {
    preferences,
    followMember,
    unfollowMember,
    followBill,
    unfollowBill,
    followTopic,
    unfollowTopic,
    followCommittee,
    unfollowCommittee,
    clearDistrictMemberMapping,
  } = useUserPreferences();
  const { resolve, isLoading: lookupLoading, error: lookupError } = useDistrictLookup();
  const [lookupText, setLookupText] = useState('');

  const districtLabel = preferences.homeDistrict?.state && preferences.homeDistrict?.district
    ? `${preferences.homeDistrict.state}-${preferences.homeDistrict.district}`
    : null;

  const feedOptions = useMemo(() => ({
    followedBills: preferences.followedBills,
    followedMembers: preferences.followedMembers,
    followedTopics: preferences.followedTopics,
    state: preferences.homeDistrict?.state,
    district: preferences.homeDistrict?.district,
    limit: 12,
  }), [
    preferences.followedBills,
    preferences.followedMembers,
    preferences.followedTopics,
    preferences.homeDistrict?.state,
    preferences.homeDistrict?.district,
  ]);
  const { items, loading: feedLoading, reload } = useFeed('myGovernment', feedOptions);

  const followedCommittees = preferences.followedCommittees ?? [];
  const followedMembers = new Set(preferences.followedMembers);
  const followedBills = new Set(preferences.followedBills);
  const followedTopics = new Set(preferences.followedTopics);
  const representative = preferences.currentMembers.find(member => member.chamber === 'House');
  const senators = preferences.currentMembers.filter(member => member.chamber === 'Senate');

  const committees = useMemo(() => collectCommittees(items), [items]);
  const bills = useMemo(() => collectBills(items), [items]);
  const topics = useMemo(() => Array.from(new Set([...defaultTopics, ...preferences.interests, ...preferences.followedTopics])), [
    preferences.interests,
    preferences.followedTopics,
  ]);

  const handleLookup = useCallback(async () => {
    const query = lookupText.trim();
    if (!query) return;
    const isZip = /^\d{5}$/.test(query);
    await resolve(isZip ? { zipCode: query } : { address: query });
  }, [lookupText, resolve]);

  const openItem = useCallback((item: FeedItem) => {
    navigation.navigate('UpdateDetail', { item });
  }, [navigation]);

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: neutral.background }]}
      contentContainerStyle={styles.scrollContent}
    >
      <View style={styles.header}>
        <Text style={[styles.eyebrow, { color: neutral.textMuted }]}>MY GOVERNMENT</Text>
        <Text style={[styles.title, { color: neutral.textPrimary }]}>
          {districtLabel ?? 'Add Your District'}
        </Text>
      </View>

      <View style={[styles.panel, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
        <View style={styles.lookupRow}>
          <TextInput
            value={lookupText}
            onChangeText={setLookupText}
            placeholder="ZIP or address"
            placeholderTextColor={neutral.textMuted}
            style={[styles.lookupInput, { color: neutral.textPrimary, borderColor: neutral.divider }]}
            autoCapitalize="words"
            returnKeyType="search"
            onSubmitEditing={handleLookup}
          />
          <Pressable
            style={[styles.lookupButton, { backgroundColor: branchColors.agency }]}
            onPress={handleLookup}
            disabled={lookupLoading}
          >
            {lookupLoading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Ionicons name="search" size={18} color="#FFFFFF" />
            )}
          </Pressable>
        </View>
        {lookupError && <Text style={[styles.warningText, { color: semantic.error }]}>{lookupError}</Text>}
        {preferences.districtLookupAmbiguity && (
          <Text style={[styles.warningText, { color: semantic.warning }]}>
            {preferences.districtLookupAmbiguity}
          </Text>
        )}
        {preferences.homeDistrict && (
          <Pressable onPress={clearDistrictMemberMapping}>
            <Text style={[styles.linkText, { color: branchColors.agency }]}>Clear district mapping</Text>
          </Pressable>
        )}
      </View>

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Representatives</Text>
        {!preferences.homeDistrict ? (
          <EmptyMessage text="Resolve a district to show your representative and senators." />
        ) : (
          <View style={styles.stack}>
            {representative && (
              <MemberRow
                member={representative}
                label="Representative"
                followed={followedMembers.has(representative.bioguide_id)}
                onToggle={() => followedMembers.has(representative.bioguide_id)
                  ? unfollowMember(representative.bioguide_id)
                  : followMember(representative.bioguide_id)}
              />
            )}
            {senators.map(senator => (
              <MemberRow
                key={senator.bioguide_id}
                member={senator}
                label="Senator"
                followed={followedMembers.has(senator.bioguide_id)}
                onToggle={() => followedMembers.has(senator.bioguide_id)
                  ? unfollowMember(senator.bioguide_id)
                  : followMember(senator.bioguide_id)}
              />
            ))}
            {preferences.currentMembers.length === 0 && (
              <EmptyMessage text="No current members are loaded for this district yet." />
            )}
          </View>
        )}
      </View>

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Followed Topics</Text>
        <View style={styles.chipWrap}>
          {topics.map(topic => {
            const active = followedTopics.has(topic);
            return (
              <Pressable
                key={topic}
                style={[
                  styles.chip,
                  {
                    backgroundColor: active ? branchColors.agency : neutral.card,
                    borderColor: active ? branchColors.agency : neutral.divider,
                  },
                ]}
                onPress={() => active ? unfollowTopic(topic) : followTopic(topic)}
              >
                <Text style={[styles.chipText, { color: active ? '#FFFFFF' : neutral.textPrimary }]}>
                  {topic}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Bills And Committees</Text>
        <View style={styles.stack}>
          {bills.map(bill => {
            const billId = bill.canonicalId;
            const active = followedBills.has(billId);
            return (
              <FollowRow
                key={billId}
                label={bill.label}
                meta={bill.title}
                followed={active}
                onToggle={() => active ? unfollowBill(billId) : followBill(billId)}
              />
            );
          })}
          {committees.map(committee => {
            const active = followedCommittees.includes(committee.id);
            return (
              <FollowRow
                key={committee.id}
                label={committee.name}
                meta={committee.jurisdiction ?? 'Committee'}
                followed={active}
                onToggle={() => active ? unfollowCommittee(committee.id) : followCommittee(committee.id)}
              />
            );
          })}
          {bills.length === 0 && committees.length === 0 && (
            <EmptyMessage text="Ranked feed cards will surface followable bills and committees here." />
          )}
        </View>
      </View>

      <View style={styles.section}>
        <View style={styles.sectionHeadingRow}>
          <Text style={[styles.sectionTitle, { color: neutral.textPrimary }]}>Recent Local Activity</Text>
          <Pressable onPress={reload}>
            <Ionicons name="refresh" size={18} color={branchColors.agency} />
          </Pressable>
        </View>
        {feedLoading && items.length === 0 ? (
          <View style={styles.inlineLoader}>
            <ActivityIndicator color={branchColors.agency} />
          </View>
        ) : (
          <View style={styles.stack}>
            {items.slice(0, 8).map(item => (
              <Pressable
                key={item.id}
                style={[styles.activityRow, { backgroundColor: neutral.card, borderColor: neutral.divider }]}
                onPress={() => openItem(item)}
              >
                <Text style={[styles.activityType, { color: branchColors[item.branch] ?? branchColors.legislative }]}>
                  {(item.card_type ?? item.branch).toUpperCase()}
                </Text>
                <Text style={[styles.activityHeadline, { color: neutral.textPrimary }]} numberOfLines={2}>
                  {item.headline}
                </Text>
                <Text style={[styles.activityMeta, { color: neutral.textMuted }]}>
                  {dayjs(item.published_at).fromNow()}
                </Text>
              </Pressable>
            ))}
            {items.length === 0 && (
              <EmptyMessage text="No recent activity matches your district or followed objects yet." />
            )}
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const MemberRow = ({
  member,
  label,
  followed,
  onToggle,
}: {
  member: CurrentMember;
  label: string;
  followed: boolean;
  onToggle: () => void;
}) => (
  <FollowRow
    label={member.name}
    meta={`${label}${member.party ? ` · ${member.party}` : ''}`}
    followed={followed}
    onToggle={onToggle}
  />
);

const FollowRow = ({
  label,
  meta,
  followed,
  onToggle,
}: {
  label: string;
  meta?: string | null;
  followed: boolean;
  onToggle: () => void;
}) => {
  const { neutral, branch } = useTheme();
  return (
    <View style={[styles.followRow, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
      <View style={styles.followText}>
        <Text style={[styles.followLabel, { color: neutral.textPrimary }]}>{label}</Text>
        {meta && <Text style={[styles.followMeta, { color: neutral.textMuted }]}>{meta}</Text>}
      </View>
      <Pressable
        style={[
          styles.followButton,
          {
            borderColor: branch.agency,
            backgroundColor: followed ? branch.agency : 'transparent',
          },
        ]}
        onPress={onToggle}
      >
        <Text style={[styles.followButtonText, { color: followed ? '#FFFFFF' : branch.agency }]}>
          {followed ? 'Following' : 'Follow'}
        </Text>
      </Pressable>
    </View>
  );
};

const EmptyMessage = ({ text }: { text: string }) => {
  const { neutral } = useTheme();
  return (
    <View style={styles.emptyBox}>
      <Text style={[styles.emptyText, { color: neutral.textSecondary }]}>{text}</Text>
    </View>
  );
};

const collectBills = (items: FeedItem[]) => {
  const byId = new Map<string, { canonicalId: string; label: string; title?: string | null }>();
  items.forEach(item => {
    const bill = item.detail?.bill;
    if (!bill) return;
    byId.set(bill.canonical_id, {
      canonicalId: bill.canonical_id,
      label: bill.display_number,
      title: bill.short_title ?? bill.title,
    });
  });
  return Array.from(byId.values());
};

const collectCommittees = (items: FeedItem[]) => {
  const byId = new Map<string, { id: string; name: string; jurisdiction?: string | null }>();
  items.forEach(item => {
    const billCommittees = item.detail?.bill?.committees ?? [];
    billCommittees.forEach(committee => {
      const id = getString(committee, 'committee_code');
      const name = getString(committee, 'name');
      if (id && name) {
        byId.set(id, { id, name, jurisdiction: getString(committee, 'jurisdiction') });
      }
    });
    const hearingCommittee = item.detail?.hearing?.committee;
    if (hearingCommittee) {
      const id = getString(hearingCommittee, 'committee_code');
      const name = getString(hearingCommittee, 'name');
      if (id && name) {
        byId.set(id, { id, name, jurisdiction: getString(hearingCommittee, 'jurisdiction') });
      }
    }
  });
  return Array.from(byId.values());
};

const getString = (value: Record<string, unknown>, key: string) => {
  const raw = value[key];
  return typeof raw === 'string' ? raw : null;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: 60,
    paddingHorizontal: 16,
    paddingBottom: 120,
    gap: 18,
  },
  header: {
    gap: 4,
  },
  eyebrow: {
    fontSize: 12,
    fontWeight: '800',
  },
  title: {
    fontSize: 32,
    fontWeight: '800',
  },
  panel: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    gap: 10,
  },
  lookupRow: {
    flexDirection: 'row',
    gap: 8,
  },
  lookupInput: {
    flex: 1,
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 15,
  },
  lookupButton: {
    width: 44,
    height: 44,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  warningText: {
    fontSize: 13,
    lineHeight: 18,
  },
  linkText: {
    fontSize: 13,
    fontWeight: '700',
  },
  section: {
    gap: 10,
  },
  sectionHeadingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '800',
  },
  stack: {
    gap: 8,
  },
  followRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  followText: {
    flex: 1,
    gap: 3,
  },
  followLabel: {
    fontSize: 15,
    fontWeight: '700',
  },
  followMeta: {
    fontSize: 12,
  },
  followButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 7,
  },
  followButtonText: {
    fontSize: 12,
    fontWeight: '800',
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  chipText: {
    fontSize: 13,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  activityRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    gap: 5,
  },
  activityType: {
    fontSize: 11,
    fontWeight: '800',
  },
  activityHeadline: {
    fontSize: 15,
    lineHeight: 20,
    fontWeight: '700',
  },
  activityMeta: {
    fontSize: 12,
  },
  inlineLoader: {
    paddingVertical: 24,
  },
  emptyBox: {
    paddingVertical: 14,
  },
  emptyText: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default YouScreen;
