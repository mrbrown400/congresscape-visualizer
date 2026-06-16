import { useCallback, useState } from 'react';

import { useUserPreferences } from '@context/UserPreferencesContext';
import { resolveDistrictMembers, DistrictLookupParams } from '@services/memberService';

export const useDistrictLookup = () => {
  const { setDistrictMemberMapping } = useUserPreferences();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const resolve = useCallback(async (params: DistrictLookupParams) => {
    setIsLoading(true);
    setError(null);
    try {
      const mapping = await resolveDistrictMembers(params);
      setDistrictMemberMapping(mapping);
      return mapping;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'District lookup failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [setDistrictMemberMapping]);

  return { resolve, isLoading, error };
};
