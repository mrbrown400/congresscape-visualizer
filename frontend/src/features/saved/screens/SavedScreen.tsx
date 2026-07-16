import React from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { useTheme } from '@theme/ThemeProvider';
import { useSavedItems } from '@context/SavedItemsContext';
import FeedCard from '@features/feed/components/FeedCard';
import { RootStackParamList } from '@navigation/RootNavigator';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

const SavedScreen = () => {
  const { neutral } = useTheme();
  const { savedItems, toggleSave, clearAll } = useSavedItems();
  const navigation = useNavigation<NavigationProp>();

  return (
    <FlatList
      data={savedItems}
      keyExtractor={item => item.id.toString()}
      contentContainerStyle={[styles.list, !savedItems.length && styles.emptyList]}
      style={{ backgroundColor: neutral.background }}
      ListHeaderComponent={savedItems.length ? (
        <View style={styles.header}>
          <Text style={[styles.title, { color: neutral.textPrimary }]}>Saved</Text>
          <Pressable onPress={clearAll} accessibilityRole="button">
            <Text style={[styles.clear, { color: neutral.textMuted }]}>Clear all</Text>
          </Pressable>
        </View>
      ) : null}
      ListEmptyComponent={
        <Text style={[styles.text, { color: neutral.textSecondary }]}>Save items from the feed to build your briefing list.</Text>
      }
      renderItem={({ item }) => (
        <FeedCard
          item={item}
          onPress={() => navigation.navigate('UpdateDetail', { item })}
          onSave={toggleSave}
          isSaved
        />
      )}
    />
  );
};

const styles = StyleSheet.create({
  list: {
    padding: 16,
    paddingBottom: 120,
  },
  emptyList: {
    flexGrow: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
  },
  clear: {
    fontSize: 14,
    fontWeight: '700',
  },
  text: {
    fontSize: 16,
    textAlign: 'center',
    paddingHorizontal: 24
  }
});

export default SavedScreen;
