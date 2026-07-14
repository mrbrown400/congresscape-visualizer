import { apiGet } from './api';
import type { DailyBrief } from '@features/dailyBrief/types';

export const fetchDailyBrief = async (date?: string): Promise<DailyBrief> => {
  return apiGet<DailyBrief>('/summary', date ? { target_date: date } : undefined);
};
