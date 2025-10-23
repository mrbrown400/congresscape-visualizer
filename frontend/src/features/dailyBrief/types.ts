import type { FeedItem } from '@features/feed/types';

export type BriefHighlight = {
  headline: string;
  summary?: string | null;
  branch: string;
  published_at: string;
  url?: string | null;
  tags: string[];
};

export type DailyBrief = {
  summary_date: string;
  generated_at: string;
  headline: string;
  narrative: string;
  highlights: BriefHighlight[];
  top_updates: FeedItem[];
};
