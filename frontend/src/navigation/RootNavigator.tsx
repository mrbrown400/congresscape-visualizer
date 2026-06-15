import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import MainTabNavigator from './MainTabNavigator';
import OnboardingScreen from '../features/onboarding/screens/OnboardingScreen';
import UpdateDetailScreen from '../features/updateDetail/screens/UpdateDetailScreen';
import NotificationSettingsScreen from '../features/settings/screens/NotificationSettingsScreen';
import { useUserPreferences } from '../context/UserPreferencesContext';
import { FeedItem } from '@features/feed/types';

export type RootStackParamList = {
  Onboarding: undefined;
  MainTabs: undefined;
  UpdateDetail: { item: FeedItem };
  NotificationSettings: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const RootNavigator = () => {
  const { hasCompletedOnboarding } = useUserPreferences();

  return (
    <Stack.Navigator
      screenOptions={{ headerShown: false }}
      initialRouteName={hasCompletedOnboarding ? 'MainTabs' : 'Onboarding'}
    >
      <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      <Stack.Screen name="MainTabs" component={MainTabNavigator} />
      <Stack.Screen
        name="UpdateDetail"
        component={UpdateDetailScreen}
        options={{
          animation: 'slide_from_right',
        }}
      />
      <Stack.Screen
        name="NotificationSettings"
        component={NotificationSettingsScreen}
        options={{
          animation: 'slide_from_right',
        }}
      />
    </Stack.Navigator>
  );
};

export default RootNavigator;
