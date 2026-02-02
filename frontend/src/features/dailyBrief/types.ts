import type { FeedItem } from '@features/feed/types';

export type BriefHighlight = {
  headline: string;
  summary?: string | null;
  branch: string;
  published_at: string;
  event_date?: string | null;
  url?: string | null;
  tags: string[];
};

export type UpcomingEvent = {
  headline: string;
  summary?: string | null;
  branch: string;
  event_date: string;
  event_type: string;
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
  upcoming_events: UpcomingEvent[];
};
