import React, { PropsWithChildren, createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

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
};

type UserPreferencesContextType = {
  preferences: UserPreferences;
  hasCompletedOnboarding: boolean;
  setInterests: (interests: string[]) => void;
  toggleInterest: (interest: string) => void;
  setNotificationPreferences: (prefs: Partial<NotificationPreferences>) => void;
  followMember: (memberId: string) => void;
  unfollowMember: (memberId: string) => void;
  followBill: (billId: string) => void;
  unfollowBill: (billId: string) => void;
  followTopic: (topic: string) => void;
  unfollowTopic: (topic: string) => void;
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
          setPreferences({ ...defaultPreferences, ...JSON.parse(storedPrefs) });
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
        setInterests,
        toggleInterest,
        setNotificationPreferences,
        followMember,
        unfollowMember,
        followBill,
        unfollowBill,
        followTopic,
        unfollowTopic,
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
