import api from './api';
import { DistrictLookupResponse } from '@features/members/types';

export type DistrictLookupParams = {
  address?: string;
  zipCode?: string;
};

export const resolveDistrictMembers = async ({ address, zipCode }: DistrictLookupParams) => {
  const response = await api.get('/members/district-lookup', {
    params: {
      address,
      zip_code: zipCode,
    },
  });
  return response.data as DistrictLookupResponse;
};
