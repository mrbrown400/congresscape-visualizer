import React from 'react';
import { Pressable, StyleSheet, Text, View, useWindowDimensions } from 'react-native';
import { BottomTabBarProps, createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';

import TodayScreen from '@features/today/screens/TodayScreen';
import CalendarScreen from '@features/calendar/screens/CalendarScreen';
import ExploreScreen from '@features/explore/screens/ExploreScreen';
import YouScreen from '@features/you/screens/YouScreen';
import { useTheme } from '@theme/ThemeProvider';

export type MainTabParamList = {
  Today: undefined;
  Calendar: undefined;
  Explore: undefined;
  You: undefined;
};

const Tab = createBottomTabNavigator<MainTabParamList>();

const tabIcons: Record<keyof MainTabParamList, keyof typeof Ionicons.glyphMap> = {
  Today: 'today',
  Calendar: 'calendar',
  Explore: 'search',
  You: 'business',
};

const tabLabels: Record<keyof MainTabParamList, string> = {
  Today: 'Today',
  Calendar: 'Calendar',
  Explore: 'Explore',
  You: 'My Gov',
};

const MainTabNavigator = () => {
  const { neutral } = useTheme();
  const { width } = useWindowDimensions();
  const isWide = width >= 900;

  return (
    <Tab.Navigator
      sceneContainerStyle={{
        backgroundColor: neutral.background,
        ...(isWide ? { marginLeft: 104 } : {}),
      }}
      tabBar={(props) => <CivicTabBar {...props} isWide={isWide} />}
      screenOptions={{
        headerShown: false,
      }}
    >
      <Tab.Screen
        name="Today"
        component={TodayScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="today" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Calendar"
        component={CalendarScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="calendar" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="Explore"
        component={ExploreScreen}
        options={{
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="search" size={size} color={color} />
          ),
        }}
      />
      <Tab.Screen
        name="You"
        component={YouScreen}
        options={{
          title: 'My Gov',
          tabBarIcon: ({ color, size }) => (
            <Ionicons name="business" size={size} color={color} />
          ),
        }}
      />
    </Tab.Navigator>
  );
};

type CivicTabBarProps = BottomTabBarProps & {
  isWide: boolean;
};

const CivicTabBar = ({ state, navigation, isWide }: CivicTabBarProps) => {
  const { neutral, branch } = useTheme();

  return (
    <View
      style={[
        styles.tabBar,
        isWide ? styles.tabBarWide : styles.tabBarMobile,
        {
          backgroundColor: neutral.card,
          borderColor: neutral.divider,
        },
      ]}
    >
      {state.routes.map((route, index) => {
        const routeName = route.name as keyof MainTabParamList;
        const focused = state.index === index;
        const color = focused ? branch.legislative : neutral.textMuted;

        const onPress = () => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });

          if (!focused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        return (
          <Pressable
            key={route.key}
            accessibilityRole="button"
            accessibilityState={focused ? { selected: true } : {}}
            onPress={onPress}
            style={[
              styles.tabItem,
              isWide ? styles.tabItemWide : styles.tabItemMobile,
            ]}
          >
            <Ionicons name={tabIcons[routeName]} size={isWide ? 22 : 28} color={color} />
            <Text style={[styles.tabLabel, { color }]}>
              {tabLabels[routeName]}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  tabBar: {
    borderWidth: 0,
  },
  tabBarMobile: {
    height: 72,
    borderTopWidth: 1,
    flexDirection: 'row',
    paddingTop: 6,
    paddingBottom: 6,
  },
  tabBarWide: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    width: 104,
    borderRightWidth: 1,
    paddingTop: 28,
    paddingBottom: 28,
  },
  tabItem: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
  },
  tabItemMobile: {
    flex: 1,
  },
  tabItemWide: {
    minHeight: 76,
    width: 104,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '800',
  },
});

export default MainTabNavigator;
