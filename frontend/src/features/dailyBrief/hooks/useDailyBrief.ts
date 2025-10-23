import { useCallback, useEffect, useState } from 'react';

import { fetchDailyBrief } from '@services/summaryService';
import type { DailyBrief } from '../types';
import type { FeedItem } from '@features/feed/types';

type DailyBriefState = {
  loading: boolean;
  error: string | null;
  brief: DailyBrief | null;
};

const initialState: DailyBriefState = {
  loading: true,
  error: null,
  brief: null
};

const normalizeSummary = (brief: DailyBrief): DailyBrief => {
  const normalizedHighlights = brief.highlights.map(highlight => ({
    ...highlight,
    summary: highlight.summary ?? ''
  }));

  const normalizedUpdates: FeedItem[] = brief.top_updates.map(update => ({
    ...update,
    summary: update.summary ?? '',
    url: update.url ?? undefined,
    metadata: update.metadata ?? undefined,
    tags: update.tags ?? []
  }));

  return {
    ...brief,
    highlights: normalizedHighlights,
    top_updates: normalizedUpdates
  };
};

export const useDailyBrief = (targetDate?: string) => {
  const [state, setState] = useState<DailyBriefState>(initialState);

  const load = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }));
    try {
      const brief = await fetchDailyBrief(targetDate);
      setState({ loading: false, error: null, brief: normalizeSummary(brief) });
    } catch (error) {
      console.warn('Failed to load daily summary', error);
      setState({
        loading: false,
        error: "Unable to load today's briefing. Try again shortly.",
        brief: null
      });
    }
  }, [targetDate]);

  useEffect(() => {
    load();
  }, [load]);

  return { ...state, reload: load };
};
