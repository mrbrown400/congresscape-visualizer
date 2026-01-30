import api from './api';

type RegisterPushPayload = {
  token: string;
  platform?: string;
  timezone?: string | null;
};

export const registerPushToken = async (payload: RegisterPushPayload) => {
  await api.post('/notifications/register', payload);
};
