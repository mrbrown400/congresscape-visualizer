import React from 'react';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';

import FeedScreen from '../features/feed/screens/FeedScreen';
import SavedScreen from '../features/saved/screens/SavedScreen';
import HearingScreen from '../features/hearings/screens/HearingScreen';
import { useTheme } from '@theme/ThemeProvider';

export type FeedTabParamList = {
  ForYou: { filter: string } | undefined;
  Legislative: { filter: string } | undefined;
  Executive: { filter: string } | undefined;
  Hearings: undefined;
  Saved: undefined;
};

const Tab = createMaterialTopTabNavigator<FeedTabParamList>();

const FeedTabs = () => {
  const { neutral, branch } = useTheme();

  return (
    <Tab.Navigator
      initialRouteName="ForYou"
      screenOptions={{
        tabBarScrollEnabled: true,
        tabBarIndicatorStyle: { backgroundColor: branch.legislative, height: 2 },
        tabBarStyle: { backgroundColor: neutral.card },
        tabBarLabelStyle: {
          color: neutral.textPrimary,
          fontWeight: '700',
          textTransform: 'none',
        },
      }}
    >
      <Tab.Screen name="ForYou" options={{ title: 'For You' }}>
        {() => <FeedScreen contextKey="forYou" />}
      </Tab.Screen>
      <Tab.Screen name="Legislative" options={{ title: 'House/Senate' }}>
        {() => <FeedScreen contextKey="legislative" />}
      </Tab.Screen>
      <Tab.Screen name="Executive">
        {() => <FeedScreen contextKey="executive" />}
      </Tab.Screen>
      <Tab.Screen name="Hearings" component={HearingScreen} />
      <Tab.Screen name="Saved" component={SavedScreen} />
    </Tab.Navigator>
  );
};

export default FeedTabs;
