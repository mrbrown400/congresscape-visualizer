import React, { PropsWithChildren, createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { CurrentMember, DistrictLookupResponse, UserDistrict } from '@features/members/types';
import { UserVotePositionValue } from '@features/votes/utils/voteComparison';

const PREFS_KEY = '@congresscape:user_preferences';
const ONBOARDING_KEY = '@congresscape:onboarding_completed';

export type NotificationPreferences = {
  dailyDigest: boolean;
  dailyDigestTime: string; // "09:00"
  breakingNews: boolean;
  billUpdates: boolean;
};

export type UserPreferences = {
  interests: string[];
  notifications: NotificationPreferences;
  followedMembers: string[];
  followedBills: string[];
  followedTopics: string[];
  followedCommittees: string[];
  billPositions: Record<string, UserBillPosition>;
  homeDistrict: UserDistrict | null;
  currentMembers: CurrentMember[];
  currentMembersUpdatedAt: string | null;
  districtLookupAmbiguity: string | null;
};

export type UserBillPosition = {
  position: UserVotePositionValue;
  updatedAt: string;
  billId: string;
  voteId?: string | null;
  sourceUrl?: string | null;
  label?: string | null;
  prompt?: string | null;
};

export type SetBillPositionOptions = {
  voteId?: string | null;
  sourceUrl?: string | null;
  label?: string | null;
  prompt?: string | null;
};

const defaultPreferences: UserPreferences = {
  interests: [],
  notifications: {
    dailyDigest: true,
    dailyDigestTime: '09:00',
    breakingNews: true,
    billUpdates: true,
  },
  followedMembers: [],
  followedBills: [],
  followedTopics: [],
  followedCommittees: [],
  billPositions: {},
  homeDistrict: null,
  currentMembers: [],
  currentMembersUpdatedAt: null,
  districtLookupAmbiguity: null,
};

type UserPreferencesContextType = {
  preferences: UserPreferences;
  hasCompletedOnboarding: boolean;
  isLoaded: boolean;
  setInterests: (interests: string[]) => void;
  toggleInterest: (interest: string) => void;
  setNotificationPreferences: (prefs: Partial<NotificationPreferences>) => void;
  followMember: (memberId: string) => void;
  unfollowMember: (memberId: string) => void;
  followBill: (billId: string) => void;
  unfollowBill: (billId: string) => void;
  followTopic: (topic: string) => void;
  unfollowTopic: (topic: string) => void;
  followCommittee: (committeeId: string) => void;
  unfollowCommittee: (committeeId: string) => void;
  setBillPosition: (billId: string, position: UserBillPosition['position'], options?: SetBillPositionOptions) => void;
  clearBillPosition: (billId: string) => void;
  clearAllBillPositions: () => void;
  setDistrictMemberMapping: (mapping: DistrictLookupResponse) => void;
  clearDistrictMemberMapping: () => void;
  completeOnboarding: () => void;
  resetOnboarding: () => void;
};

const UserPreferencesContext = createContext<UserPreferencesContextType | undefined>(undefined);

export const UserPreferencesProvider = ({ children }: PropsWithChildren) => {
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load preferences from storage
  useEffect(() => {
    const load = async () => {
      try {
        const [storedPrefs, storedOnboarding] = await Promise.all([
          AsyncStorage.getItem(PREFS_KEY),
          AsyncStorage.getItem(ONBOARDING_KEY),
        ]);
        if (storedPrefs) {
          setPreferences(normalizePreferences(JSON.parse(storedPrefs)));
        }
        if (storedOnboarding === 'true') {
          setHasCompletedOnboarding(true);
        }
      } catch (e) {
        console.warn('Failed to load preferences:', e);
      } finally {
        setIsLoaded(true);
      }
    };
    load();
  }, []);

  // Persist preferences
  useEffect(() => {
    if (!isLoaded) return;
    const persist = async () => {
      try {
        await AsyncStorage.setItem(PREFS_KEY, JSON.stringify(preferences));
      } catch (e) {
        console.warn('Failed to persist preferences:', e);
      }
    };
    persist();
  }, [preferences, isLoaded]);

  const setInterests = useCallback((interests: string[]) => {
    setPreferences(prev => ({ ...prev, interests }));
  }, []);

  const toggleInterest = useCallback((interest: string) => {
    setPreferences(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  }, []);

  const setNotificationPreferences = useCallback((prefs: Partial<NotificationPreferences>) => {
    setPreferences(prev => ({
      ...prev,
      notifications: { ...prev.notifications, ...prefs }
    }));
  }, []);

  const followMember = useCallback((memberId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedMembers: prev.followedMembers.includes(memberId)
        ? prev.followedMembers
        : [...prev.followedMembers, memberId]
    }));
  }, []);

  const unfollowMember = useCallback((memberId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedMembers: prev.followedMembers.filter(id => id !== memberId)
    }));
  }, []);

  const followBill = useCallback((billId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedBills: prev.followedBills.includes(billId)
        ? prev.followedBills
        : [...prev.followedBills, billId]
    }));
  }, []);

  const unfollowBill = useCallback((billId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedBills: prev.followedBills.filter(id => id !== billId)
    }));
  }, []);

  const followTopic = useCallback((topic: string) => {
    setPreferences(prev => ({
      ...prev,
      followedTopics: prev.followedTopics.includes(topic)
        ? prev.followedTopics
        : [...prev.followedTopics, topic]
    }));
  }, []);

  const unfollowTopic = useCallback((topic: string) => {
    setPreferences(prev => ({
      ...prev,
      followedTopics: prev.followedTopics.filter(t => t !== topic)
    }));
  }, []);

  const followCommittee = useCallback((committeeId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedCommittees: prev.followedCommittees.includes(committeeId)
        ? prev.followedCommittees
        : [...prev.followedCommittees, committeeId]
    }));
  }, []);

  const unfollowCommittee = useCallback((committeeId: string) => {
    setPreferences(prev => ({
      ...prev,
      followedCommittees: prev.followedCommittees.filter(id => id !== committeeId)
    }));
  }, []);

  const setBillPosition = useCallback((
    billId: string,
    position: UserBillPosition['position'],
    options: SetBillPositionOptions = {},
  ) => {
    setPreferences(prev => ({
      ...prev,
      billPositions: {
        ...prev.billPositions,
        [billId]: {
          position,
          updatedAt: new Date().toISOString(),
          billId,
          voteId: options.voteId ?? null,
          sourceUrl: options.sourceUrl ?? null,
          label: options.label ?? null,
          prompt: options.prompt ?? null,
        },
      },
    }));
  }, []);

  const clearBillPosition = useCallback((billId: string) => {
    setPreferences(prev => {
      const nextPositions = { ...prev.billPositions };
      delete nextPositions[billId];
      return { ...prev, billPositions: nextPositions };
    });
  }, []);

  const clearAllBillPositions = useCallback(() => {
    setPreferences(prev => ({ ...prev, billPositions: {} }));
  }, []);

  const setDistrictMemberMapping = useCallback((mapping: DistrictLookupResponse) => {
    setPreferences(prev => ({
      ...prev,
      homeDistrict: {
        state: mapping.state ?? null,
        district: mapping.district ?? null,
        lookupKey: mapping.lookup_key,
        lookupType: mapping.lookup_type,
        query: mapping.query,
        source: mapping.source,
        retrievedAt: mapping.retrieved_at,
        ambiguityReason: mapping.ambiguity_reason ?? null,
      },
      currentMembers: [
        ...(mapping.representative ? [mapping.representative] : []),
        ...mapping.senators,
      ],
      currentMembersUpdatedAt: mapping.retrieved_at,
      districtLookupAmbiguity: mapping.ambiguity_reason ?? null,
    }));
  }, []);

  const clearDistrictMemberMapping = useCallback(() => {
    setPreferences(prev => ({
      ...prev,
      homeDistrict: null,
      currentMembers: [],
      currentMembersUpdatedAt: null,
      districtLookupAmbiguity: null,
    }));
  }, []);

  const completeOnboarding = useCallback(async () => {
    setHasCompletedOnboarding(true);
    try {
      await AsyncStorage.setItem(ONBOARDING_KEY, 'true');
    } catch (e) {
      console.warn('Failed to persist onboarding state:', e);
    }
  }, []);

  const resetOnboarding = useCallback(async () => {
    setHasCompletedOnboarding(false);
    try {
      await AsyncStorage.removeItem(ONBOARDING_KEY);
    } catch (e) {
      console.warn('Failed to reset onboarding state:', e);
    }
  }, []);

  return (
    <UserPreferencesContext.Provider
      value={{
        preferences,
        hasCompletedOnboarding,
        isLoaded,
        setInterests,
        toggleInterest,
        setNotificationPreferences,
        followMember,
        unfollowMember,
        followBill,
        unfollowBill,
        followTopic,
        unfollowTopic,
        followCommittee,
        unfollowCommittee,
        setBillPosition,
        clearBillPosition,
        clearAllBillPositions,
        setDistrictMemberMapping,
        clearDistrictMemberMapping,
        completeOnboarding,
        resetOnboarding,
      }}
    >
      {children}
    </UserPreferencesContext.Provider>
  );
};

export const useUserPreferences = () => {
  const ctx = useContext(UserPreferencesContext);
  if (!ctx) {
    throw new Error('useUserPreferences must be used within UserPreferencesProvider');
  }
  return ctx;
};

const normalizePreferences = (stored: Partial<UserPreferences>): UserPreferences => {
  const merged = {
    ...defaultPreferences,
    ...stored,
    notifications: {
      ...defaultPreferences.notifications,
      ...(stored.notifications ?? {}),
    },
  };

  return {
    ...merged,
    billPositions: normalizeBillPositions(stored.billPositions),
  };
};

const normalizeBillPositions = (
  positions: Partial<Record<string, Partial<UserBillPosition>>> | undefined,
): Record<string, UserBillPosition> => {
  if (!positions) return {};

  return Object.entries(positions).reduce<Record<string, UserBillPosition>>((acc, [key, value]) => {
    if (!value?.position) return acc;
    acc[key] = {
      position: value.position,
      updatedAt: value.updatedAt ?? new Date().toISOString(),
      billId: value.billId ?? key,
      voteId: value.voteId ?? null,
      sourceUrl: value.sourceUrl ?? null,
      label: value.label ?? null,
      prompt: value.prompt ?? null,
    };
    return acc;
  }, {});
};
