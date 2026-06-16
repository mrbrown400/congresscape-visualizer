import { UserBillPosition } from '@context/UserPreferencesContext';
import { BillDetail, FeedItem, VoteDetail } from '@features/feed/types';

export type VoteSubject = {
  subjectId: string;
  billId?: string | null;
  voteId?: string | null;
  label: string;
  prompt: string;
  sourceUrl?: string | null;
};

export const personalVotePrompt =
  'Record a personal position for comparison. This is civic tracking, not an official congressional vote.';

export const localVotePrivacyCopy =
  'Stored only on this device for personal comparison. It is not sent to Congress or posted publicly.';

export const getVoteSubjectForItem = (item: FeedItem): VoteSubject | null => {
  if (item.detail?.vote) return getVoteSubjectForVote(item.detail.vote);
  if (item.detail?.bill) return getVoteSubjectForBill(item.detail.bill);
  return null;
};

export const getVoteSubjectForBill = (bill: BillDetail): VoteSubject | null => {
  if (!bill.vote_eligible) return null;
  const firstVote = bill.votes.find(vote => getRecordString(vote, 'canonical_id'));
  return {
    subjectId: bill.canonical_id,
    billId: bill.canonical_id,
    voteId: firstVote ? getRecordString(firstVote, 'canonical_id') : null,
    label: bill.display_number,
    prompt: bill.user_position_prompt ?? personalVotePrompt,
    sourceUrl: bill.source_url,
  };
};

export const getVoteSubjectForVote = (vote: VoteDetail): VoteSubject => {
  const billId = getRecordString(vote.linked_bill, 'canonical_id');
  const billLabel = getRecordString(vote.linked_bill, 'display_number');
  return {
    subjectId: billId ?? vote.canonical_id,
    billId,
    voteId: vote.canonical_id,
    label: billLabel ?? `${vote.chamber} roll call ${vote.roll_number}`,
    prompt: personalVotePrompt,
    sourceUrl: vote.source_url,
  };
};

export const findLedgerEntry = (
  ledger: Record<string, UserBillPosition>,
  subjectId?: string | null,
  voteId?: string | null,
): UserBillPosition | null => {
  if (subjectId && ledger[subjectId]) return ledger[subjectId];
  if (!voteId) return null;
  return Object.values(ledger).find(entry => entry.voteId === voteId) ?? null;
};

export const getRecordString = (record: Record<string, unknown> | null | undefined, key: string) => {
  const raw = record?.[key];
  return typeof raw === 'string' ? raw : null;
};
