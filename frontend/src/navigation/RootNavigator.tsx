import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import DailyBriefScreen from '@features/dailyBrief/screens/DailyBriefScreen';
import OnboardingScreen from '../features/onboarding/screens/OnboardingScreen';

export type RootStackParamList = {
  Onboarding: undefined;
  Main: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

const RootNavigator = () => {
  // Wire in persisted onboarding completion later; default to showing onboarding first for now.
  const hasCompletedOnboarding = false;

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      {!hasCompletedOnboarding && (
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
      )}
      <Stack.Screen name="Main" component={DailyBriefScreen} />
    </Stack.Navigator>
  );
};

export default RootNavigator;
