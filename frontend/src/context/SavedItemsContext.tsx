import React, { PropsWithChildren, createContext, useCallback, useContext, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { FeedItem } from '@features/feed/types';

const STORAGE_KEY = '@congresscape:saved_items';

type SavedItemsContextType = {
  savedItems: FeedItem[];
  isSaved: (id: number) => boolean;
  toggleSave: (item: FeedItem) => void;
  clearAll: () => void;
};

const SavedItemsContext = createContext<SavedItemsContextType | undefined>(undefined);

export const SavedItemsProvider = ({ children }: PropsWithChildren) => {
  const [savedItems, setSavedItems] = useState<FeedItem[]>([]);

  // Load saved items from storage on mount
  useEffect(() => {
    const load = async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) {
          setSavedItems(JSON.parse(stored));
        }
      } catch (e) {
        console.warn('Failed to load saved items:', e);
      }
    };
    load();
  }, []);

  // Persist to storage whenever savedItems changes
  useEffect(() => {
    const persist = async () => {
      try {
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(savedItems));
      } catch (e) {
        console.warn('Failed to persist saved items:', e);
      }
    };
    persist();
  }, [savedItems]);

  const isSaved = useCallback((id: number) => {
    return savedItems.some(item => item.id === id);
  }, [savedItems]);

  const toggleSave = useCallback((item: FeedItem) => {
    setSavedItems(prev => {
      const exists = prev.some(i => i.id === item.id);
      if (exists) {
        return prev.filter(i => i.id !== item.id);
      }
      return [item, ...prev];
    });
  }, []);

  const clearAll = useCallback(() => {
    setSavedItems([]);
  }, []);

  return (
    <SavedItemsContext.Provider value={{ savedItems, isSaved, toggleSave, clearAll }}>
      {children}
    </SavedItemsContext.Provider>
  );
};

export const useSavedItems = () => {
  const ctx = useContext(SavedItemsContext);
  if (!ctx) {
    throw new Error('useSavedItems must be used within SavedItemsProvider');
  }
  return ctx;
};
