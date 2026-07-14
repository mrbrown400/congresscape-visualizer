import { apiGet } from './api';
import { FeedItem } from '@features/feed/types';

export const fetchFeed = async (params: Record<string, string | number | undefined>) => {
  return apiGet<{ items: FeedItem[]; total: number }>('/feed', params);
};
