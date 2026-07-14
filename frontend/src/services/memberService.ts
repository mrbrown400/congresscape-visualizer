import { apiGet } from './api';
import { DistrictLookupResponse } from '@features/members/types';

export type DistrictLookupParams = {
  address?: string;
  zipCode?: string;
};

export const resolveDistrictMembers = async ({ address, zipCode }: DistrictLookupParams) => {
  return apiGet<DistrictLookupResponse>('/members/district-lookup', {
    address,
    zip_code: zipCode,
  });
};
