import { useCallback, useEffect, useState } from 'react';

import { fetchFeed } from '@services/feedService';
import { CivicCardType, FeedItem, FeedScope } from '../types';

type FeedState = {
  loading: boolean;
  error: string | null;
  items: FeedItem[];
  total: number;
};

export type FeedContextOptions = {
  followedBills?: string[];
  followedMembers?: string[];
  followedTopics?: string[];
  followedCommittees?: string[];
  state?: string | null;
  district?: string | null;
  cardType?: CivicCardType;
  scope?: FeedScope;
  jurisdiction?: string | null;
  limit?: number;
};

const initialState: FeedState = {
  loading: true,
  error: null,
  items: [],
  total: 0
};

const defaultFeedOptions: FeedContextOptions = {};

export const useFeed = (contextKey: string, options: FeedContextOptions = defaultFeedOptions) => {
  const [state, setState] = useState<FeedState>(initialState);

  const load = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const params = mapContextToParams(contextKey, options);
      const data = await fetchFeed(params);
      setState({ loading: false, error: null, items: data.items, total: data.total });
    } catch (error) {
      console.warn('Failed to load feed', error);
      setState({ loading: false, error: 'Unable to load feed right now.', items: [], total: 0 });
    }
  }, [contextKey, options]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, reload: load };
};

const mapContextToParams = (contextKey: string, options: FeedContextOptions) => {
  const base = {
    followed_bills: options.followedBills?.join(',') || undefined,
    followed_members: options.followedMembers?.join(',') || undefined,
    followed_topics: options.followedTopics?.join(',') || undefined,
    followed_committees: options.followedCommittees?.join(',') || undefined,
    state: options.state ?? undefined,
    district: options.district ?? undefined,
    card_type: options.cardType,
    scope: options.scope,
    jurisdiction: options.jurisdiction ?? undefined,
    limit: options.limit,
  };

  switch (contextKey) {
    case 'today':
      return {
        ...base,
        scope: options.scope ?? 'local',
        jurisdiction: options.jurisdiction ?? 'la',
        limit: options.limit ?? 20,
      };
    case 'local':
    case 'all':
    case 'forYou':
    case 'myGovernment':
      return {
        ...base,
        scope: options.scope ?? 'local',
        jurisdiction: options.jurisdiction ?? 'la',
        limit: options.limit ?? 20,
      };
    case 'city':
      return { ...base, scope: 'local', jurisdiction: 'la.city', limit: options.limit ?? 30 };
    case 'county':
      return { ...base, scope: 'local', jurisdiction: 'la.county', limit: options.limit ?? 30 };
    case 'metro':
      return { ...base, scope: 'local', jurisdiction: 'la.metro', limit: options.limit ?? 30 };
    case 'federal':
      return { ...base, scope: 'federal', limit: options.limit ?? 30 };
    case 'meetings':
      return { ...base, scope: 'local', jurisdiction: options.jurisdiction ?? 'la', card_type: 'hearing', limit: options.limit ?? 30 };
    case 'actions':
      return { ...base, scope: 'local', jurisdiction: options.jurisdiction ?? 'la', card_type: 'vote', limit: options.limit ?? 30 };
    case 'legislative':
      return { ...base, branch: 'legislative', limit: options.limit ?? 30 };
    case 'votes':
      return { ...base, branch: 'legislative', card_type: 'vote', limit: options.limit ?? 30 };
    case 'hearings':
      return { ...base, branch: 'legislative', card_type: 'hearing', limit: options.limit ?? 30 };
    case 'executive':
      return { ...base, branch: 'executive', limit: options.limit ?? 30 };
    case 'judicial':
      return { ...base, branch: 'judicial', limit: options.limit ?? 30 };
    default:
      return { ...base, limit: options.limit ?? 20 };
  }
};
