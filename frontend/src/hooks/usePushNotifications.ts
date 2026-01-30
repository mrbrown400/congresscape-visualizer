import { useEffect } from 'react';
import * as Device from 'expo-device';
import * as Notifications from 'expo-notifications';
import Constants from 'expo-constants';

import { registerPushToken } from '@services/notificationService';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: false,
    shouldSetBadge: false
  })
});

let hasRegistered = false;

const resolveProjectId = () => {
  const expoConfigProjectId = Constants.expoConfig?.extra?.eas?.projectId;
  if (expoConfigProjectId) {
    return expoConfigProjectId;
  }
  return Constants.easConfig?.projectId;
};

export const usePushNotifications = () => {
  useEffect(() => {
    const register = async () => {
      if (hasRegistered) {
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
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      });

      hasRegistered = true;
    };

    register().catch(error => {
      console.warn('Unable to register for push notifications', error);
    });
  }, []);
};
