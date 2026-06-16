export type Branch = 'house' | 'senate' | 'legislative' | 'judicial' | 'executive' | 'agency';

export type CivicCardType = 'bill' | 'vote' | 'hearing' | 'money' | 'alert';

export type SourceTrailStatus = 'available' | 'pending' | 'unavailable';

export type MoneyContextStatus = 'available' | 'not_applicable' | 'pending' | 'unavailable';

export type MoneySourceRelationship =
  | 'direct_source'
  | 'related_entity'
  | 'topic_context'
  | 'unavailable';

export type SourceCategory = 'official' | 'fallback' | 'supporting' | 'unavailable';

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
  confidence?: MoneySourceRelationship;
  source_category?: SourceCategory;
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
  confidence_label?: {
    relationship: MoneySourceRelationship;
    label: string;
    description: string;
  } | null;
  source_indexes: number[];
  unavailable_reason?: string | null;
  note?: string | null;
  status?: MoneyContextStatus | null;
  source_system?: string | null;
  source_category?: SourceCategory | null;
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

export type RankContext = {
  score: number;
  factors: Record<string, number>;
  reasons: string[];
};

export type SourceTrailItem = CivicSource & {
  confidence?: string;
  source_category?: string;
};

export type BillTimelineItem = {
  id: number;
  action_type?: string | null;
  text: string;
  acted_at?: string | null;
  chamber?: string | null;
  source_url?: string | null;
};

export type BillDetail = {
  canonical_id: string;
  display_number: string;
  title: string;
  short_title?: string | null;
  status: string;
  origin_chamber?: string | null;
  policy_area?: string | null;
  introduced_at?: string | null;
  latest_action_at?: string | null;
  sponsors: Record<string, unknown>[];
  cosponsors: Record<string, unknown>[];
  committees: Record<string, unknown>[];
  timeline: BillTimelineItem[];
  text_versions: Record<string, unknown>[];
  amendments: Record<string, unknown>[];
  related_bills: Record<string, unknown>[];
  cbo_cost_estimates: Record<string, unknown>[];
  crs_reports: Record<string, unknown>[];
  votes: Record<string, unknown>[];
  vote_eligible: boolean;
  money_context_status?: MoneyContextStatus;
  money_context_note?: string | null;
  money_context?: CivicMoneyContextItem[];
  user_position_prompt?: string | null;
  source_url?: string | null;
  unavailable: Record<string, string | null>;
};

export type VotePosition = {
  member_identifier: string;
  member_name: string;
  party?: string | null;
  state?: string | null;
  district?: string | null;
  position: string;
  congress_url?: string | null;
  is_current_member?: boolean | null;
};

export type VoteDetail = {
  canonical_id: string;
  chamber: string;
  congress: number;
  session?: string | null;
  roll_number: string;
  vote_date?: string | null;
  question: string;
  result?: string | null;
  margin?: string | null;
  totals: Record<string, unknown>;
  party_split: Record<string, unknown>;
  positions: VotePosition[];
  local_representative_positions: VotePosition[];
  linked_bill?: Record<string, unknown> | null;
  source_url?: string | null;
  unavailable: Record<string, string | null>;
};

export type HearingDetail = {
  canonical_id: string;
  event_id: string;
  congress?: number | null;
  chamber: string;
  title: string;
  meeting_type?: string | null;
  status?: string | null;
  scheduled_at?: string | null;
  location?: string | null;
  committee?: Record<string, unknown> | null;
  witnesses: Record<string, unknown>[];
  related_bills: Record<string, unknown>[];
  videos: Record<string, unknown>[];
  transcripts: Record<string, unknown>[];
  source_url?: string | null;
  follow_supported: boolean;
  alert_affordance?: string | null;
  unavailable: Record<string, string | null>;
};

export type FeedItemDetail = {
  bill?: BillDetail;
  vote?: VoteDetail;
  hearing?: HearingDetail;
};

export type FeedItem = {
  id: number;
  external_id?: string;
  headline: string;
  summary?: string | null;
  full_text?: string | null;
  published_at: string;
  event_date?: string | null;
  branch: Branch;
  source: string;
  url?: string;
  bill_id?: number | null;
  bill_action_id?: number | null;
  vote_id?: number | null;
  hearing_id?: number | null;
  tags: string[];
  card_type?: CivicCardType;
  rank_context?: RankContext;
  involved?: CivicEntity[];
  key_claims?: CivicClaim[];
  source_trail?: SourceTrailItem[];
  source_trail_status?: SourceTrailStatus;
  source_trail_note?: string | null;
  money_context_status?: MoneyContextStatus;
  money_context_note?: string | null;
  money_context?: CivicMoneyContextItem[];
  detail?: FeedItemDetail;
  entities?: { id: number; name: string; type: string; slug: string }[];
  metadata?: Record<string, unknown> | null;
};
