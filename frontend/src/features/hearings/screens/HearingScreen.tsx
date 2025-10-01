import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

const HearingScreen = () => (
  <View style={styles.container}>
    <Text style={styles.text}>Committee hearings schedule coming soon.</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#040C1A'
  },
  text: {
    color: '#C7D2FE',
    fontSize: 16
  }
});

export default HearingScreen;
