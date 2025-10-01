import React from 'react';
import { createMaterialTopTabNavigator } from '@react-navigation/material-top-tabs';

import FeedScreen from '../features/feed/screens/FeedScreen';
import SavedScreen from '../features/saved/screens/SavedScreen';
import HearingScreen from '../features/hearings/screens/HearingScreen';

export type FeedTabParamList = {
  Trending: { filter: string } | undefined;
  Urgent: { filter: string } | undefined;
  ForYou: { filter: string } | undefined;
  Legislative: { filter: string } | undefined;
  Executive: { filter: string } | undefined;
  Hearings: undefined;
  Saved: undefined;
};

const Tab = createMaterialTopTabNavigator<FeedTabParamList>();

const FeedTabs = () => (
  <Tab.Navigator
    initialRouteName="ForYou"
    screenOptions={{
      tabBarScrollEnabled: true,
      tabBarIndicatorStyle: { backgroundColor: '#F59E0B' },
      tabBarStyle: { backgroundColor: '#0B1D3A' },
      tabBarLabelStyle: { color: '#F8FAFC', fontWeight: '600', textTransform: 'none' }
    }}
  >
    <Tab.Screen name="ForYou" options={{ title: 'For You' }}>
      {() => <FeedScreen contextKey="forYou" />}
    </Tab.Screen>
    <Tab.Screen name="Trending">
      {() => <FeedScreen contextKey="trending" />}
    </Tab.Screen>
    <Tab.Screen name="Urgent">
      {() => <FeedScreen contextKey="urgent" />}
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

export default FeedTabs;
