export type Branch = 'house' | 'senate' | 'legislative' | 'judicial' | 'executive' | 'agency';

export type CivicCardType = 'bill' | 'vote' | 'hearing' | 'money' | 'alert';

export type SourceTrailStatus = 'available' | 'pending' | 'unavailable';

export type MoneyContextStatus = 'available' | 'not_applicable' | 'pending' | 'unavailable';

export type MoneySourceRelationship =
  | 'direct_source'
  | 'related_entity'
  | 'topic_context'
  | 'unavailable';

export type CivicEntity = {
  name: string;
  entity_type: string;
  role?: string | null;
  identifier?: string | null;
  url?: string | null;
};

export type CivicSource = {
  label: string;
  source: string;
  url: string;
  published_at?: string | null;
  retrieved_at?: string | null;
  supports: string[];
};

export type CivicClaim = {
  id: string;
  text: string;
  source_indexes: number[];
  unavailable_reason?: string | null;
};

export type CivicMoneyContextItem = {
  label: string;
  value?: string | null;
  source_relationship: MoneySourceRelationship;
  source_indexes: number[];
  unavailable_reason?: string | null;
  note?: string | null;
};

export type CivicCard = {
  id: string;
  card_type: CivicCardType;
  branch: Branch;
  source: string;
  headline: string;
  summary: string;
  what_happened: string;
  published_at: string;
  last_updated_at: string;
  event_date?: string | null;
  primary_update_id?: number | null;
  why_it_matters?: string | null;
  involved: CivicEntity[];
  key_claims: CivicClaim[];
  money_context_status: MoneyContextStatus;
  money_context_note?: string | null;
  money_context: CivicMoneyContextItem[];
  source_trail_status: SourceTrailStatus;
  source_trail_note?: string | null;
  source_trail: CivicSource[];
  tags: string[];
  metadata?: Record<string, unknown> | null;
};

export type FeedItem = {
  id: number;
  headline: string;
  summary: string;
  published_at: string;
  branch: Branch;
  source: string;
  url?: string;
  tags: string[];
  metadata?: Record<string, unknown>;
};
