import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

import { useTheme } from '@theme/ThemeProvider';

const HearingScreen = () => {
  const { neutral } = useTheme();

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      <Text style={[styles.text, { color: neutral.textSecondary }]}>
        Committee hearings schedule coming soon.
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
    fontSize: 16
  }
});

export default HearingScreen;
