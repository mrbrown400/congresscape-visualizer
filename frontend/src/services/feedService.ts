import api from './api';
import { FeedItem } from '@features/feed/types';

export const fetchFeed = async (params: Record<string, string | number | undefined>) => {
  const response = await api.get('/feed', { params });
  return response.data as { items: FeedItem[]; total: number };
};
