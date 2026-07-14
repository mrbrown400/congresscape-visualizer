import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@theme/ThemeProvider';

const SavedScreen = () => {
  const { neutral } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      <Text style={[styles.text, { color: neutral.textSecondary }]}>
        Save items from the feed to build your briefing list.
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 24
  }
});

export default SavedScreen;
