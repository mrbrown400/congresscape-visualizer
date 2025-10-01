export type Branch = 'house' | 'senate' | 'legislative' | 'judicial' | 'executive' | 'agency';

export type FeedItem = {
  id: number;
  headline: string;
  summary: string;
  published_at: string;
  branch: Branch;
  source: string;
  url?: string;
  tags: string[];
  metadata?: Record<string, unknown>;
};
