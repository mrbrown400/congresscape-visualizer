import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

import RootNavigator from './src/navigation/RootNavigator';
import { ThemeProvider } from './src/theme/ThemeProvider';
import { SavedItemsProvider } from './src/context/SavedItemsContext';
import { UserPreferencesProvider } from './src/context/UserPreferencesContext';
import { usePushNotifications } from './src/hooks/usePushNotifications';

export default function App() {
  usePushNotifications();

  return (
    <SafeAreaProvider>
      <UserPreferencesProvider>
        <SavedItemsProvider>
          <ThemeProvider>
            <NavigationContainer>
              <RootNavigator />
            </NavigationContainer>
          </ThemeProvider>
        </SavedItemsProvider>
      </UserPreferencesProvider>
    </SafeAreaProvider>
  );
}
