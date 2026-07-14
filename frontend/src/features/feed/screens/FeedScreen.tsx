import React, { useCallback } from 'react';
import { ActivityIndicator, FlatList, RefreshControl, StyleSheet, Text, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import FeedCard from '@features/feed/components/FeedCard';
import { useFeed } from '@features/feed/hooks/useFeed';
import { RootStackParamList } from '@navigation/RootNavigator';
import { useTheme } from '@theme/ThemeProvider';

import { FeedItem } from '../types';

type NavigationProp = NativeStackNavigationProp<RootStackParamList>;

type Props = {
  contextKey: string;
};

const FeedScreen = ({ contextKey }: Props) => {
  const { neutral, branch } = useTheme();
  const { items, loading, error, reload } = useFeed(contextKey);
  const navigation = useNavigation<NavigationProp>();

  const renderItem = useCallback(({ item }: { item: FeedItem }) => (
    <FeedCard item={item} onPress={() => navigation.navigate('UpdateDetail', { item })} />
  ), [navigation]);

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}> 
      {loading && items.length === 0 ? (
        <View style={styles.loader}>
          <ActivityIndicator size="large" color={branch.legislative} />
          <Text style={[styles.loaderText, { color: neutral.textSecondary }]}>
            Loading {contextKey} updates...
          </Text>
        </View>
      ) : (
        <FlatList
          data={items}
          renderItem={renderItem}
          keyExtractor={item => item.id.toString()}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={loading} onRefresh={reload} tintColor={branch.legislative} />}
          ListEmptyComponent={
            error ? (
              <Text style={[styles.errorText, { color: '#B91C1C' }]}>{error}</Text>
            ) : (
              <Text style={[styles.emptyText, { color: neutral.textMuted }]}>No updates yet. Check back soon.</Text>
            )
          }
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 12,
  },
  listContent: {
    width: '100%',
    maxWidth: 1040,
    alignSelf: 'center',
    paddingBottom: 120,
  },
  loader: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12
  },
  loaderText: {
    fontSize: 16,
  },
  errorText: {
    textAlign: 'center',
    marginTop: 24,
  },
  emptyText: {
    textAlign: 'center',
    marginTop: 24,
  }
});

export default FeedScreen;
