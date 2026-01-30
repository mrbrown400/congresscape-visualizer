import api from './api';
import type { DailyBrief } from '@features/dailyBrief/types';

export const fetchDailyBrief = async (date?: string): Promise<DailyBrief> => {
  const response = await api.get('/summary', { params: date ? { target_date: date } : undefined });
  return response.data as DailyBrief;
};
