import { apiPost } from './api';

type RegisterPushPayload = {
  token: string;
  platform?: string;
  timezone?: string | null;
  followed_bills?: string[];
  followed_members?: string[];
  followed_topics?: string[];
  followed_committees?: string[];
  alert_categories?: {
    bill_movement: boolean;
    representative_votes: boolean;
    hearing_tomorrow: boolean;
    new_text: boolean;
    money_context: boolean;
  };
};

export const registerPushToken = async (payload: RegisterPushPayload) => {
  await apiPost('/notifications/register', payload);
};
