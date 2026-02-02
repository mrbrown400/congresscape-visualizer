import { useCallback, useEffect, useState } from 'react';

import { fetchFeed } from '@services/feedService';
import { mockFeed } from '@features/feed/data/mockFeed';
import { FeedItem } from '../types';

type FeedState = {
  loading: boolean;
  error: string | null;
  items: FeedItem[];
  total: number;
};

const initialState: FeedState = {
  loading: true,
  error: null,
  items: [],
  total: 0
};

export const useFeed = (contextKey: string) => {
  const [state, setState] = useState<FeedState>(initialState);

  const load = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const params = mapContextToParams(contextKey);
      const data = await fetchFeed(params);
      setState({ loading: false, error: null, items: data.items, total: data.total });
    } catch (error) {
      console.warn('Failed to load feed', error);
      setState({ loading: false, error: 'Unable to load feed right now.', items: mockFeed, total: mockFeed.length });
    }
  }, [contextKey]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, reload: load };
};

const mapContextToParams = (contextKey: string) => {
  switch (contextKey) {
    case 'trending':
      return { sort: 'trending', limit: 20 };
    case 'urgent':
      return { sort: 'urgent', limit: 20 };
    case 'legislative':
      return { branch: 'legislative', limit: 30 };
    case 'executive':
      return { branch: 'executive', limit: 30 };
    case 'judicial':
      return { branch: 'judicial', limit: 30 };
    default:
      return { limit: 20 };
  }
};
