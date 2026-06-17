import { useEffect } from 'react';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

import { useUserPreferences } from '@context/UserPreferencesContext';
import { registerPushToken } from '@services/notificationService';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: false,
    shouldSetBadge: false
  })
});

let lastRegistrationKey: string | null = null;

const resolveProjectId = () => {
  const expoConfigProjectId = Constants.expoConfig?.extra?.eas?.projectId;
  if (expoConfigProjectId) {
    return expoConfigProjectId;
  }
  return Constants.easConfig?.projectId;
};

export const usePushNotifications = () => {
  const { preferences, isLoaded } = useUserPreferences();

  useEffect(() => {
    const register = async () => {
      if (!isLoaded) {
        return;
      }

      const registrationState = {
        followed_bills: preferences.followedBills,
        followed_members: preferences.followedMembers,
        followed_topics: preferences.followedTopics,
        followed_committees: preferences.followedCommittees,
        alert_categories: {
          bill_movement: preferences.notifications.billUpdates,
          representative_votes: preferences.notifications.representativeVotes,
          hearing_tomorrow: preferences.notifications.hearingAlerts,
          new_text: preferences.notifications.textAlerts,
          money_context: preferences.notifications.moneyContextAlerts,
        },
      };
      const registrationKey = JSON.stringify(registrationState);
      if (lastRegistrationKey === registrationKey) {
        return;
      }

      if (!Device.isDevice) {
        console.info('Push notifications require a physical device.');
        return;
      }

      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.warn('Push notification permissions were not granted.');
        return;
      }

      const projectId = resolveProjectId();
      const pushToken = await Notifications.getExpoPushTokenAsync(
        projectId ? { projectId } : undefined
      );

      await registerPushToken({
        token: pushToken.data,
        platform: 'expo',
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        ...registrationState,
      });

      lastRegistrationKey = registrationKey;
    };

    register().catch(error => {
      console.warn('Unable to register for push notifications', error);
    });
  }, [isLoaded, preferences]);
};
