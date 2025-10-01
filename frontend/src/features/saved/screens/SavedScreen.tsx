import React from 'react';
import { StyleSheet, Text, View } from 'react-native';

const SavedScreen = () => (
  <View style={styles.container}>
    <Text style={styles.text}>Save items from the feed to build your briefing list.</Text>
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
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 24
  }
});

export default SavedScreen;
