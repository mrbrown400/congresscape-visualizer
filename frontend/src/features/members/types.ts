export type UserDistrict = {
  state: string | null;
  district: string | null;
  lookupKey: string;
  lookupType: string;
  query: string;
  source: string;
  retrievedAt: string;
  ambiguityReason?: string | null;
};

export type CurrentMember = {
  id: number;
  bioguide_id: string;
  name: string;
  party?: string | null;
  state?: string | null;
  district?: string | null;
  chamber?: string | null;
  member_type?: string | null;
  current: boolean;
  congress_url?: string | null;
  identifiers: Record<string, unknown>;
};

export type DistrictLookupResponse = {
  lookup_key: string;
  lookup_type: string;
  query: string;
  state?: string | null;
  district?: string | null;
  source: string;
  retrieved_at: string;
  ambiguity_reason?: string | null;
  representative?: CurrentMember | null;
  senators: CurrentMember[];
};
