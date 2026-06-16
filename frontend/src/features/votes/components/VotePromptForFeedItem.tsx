import React from 'react';

import { FeedItem } from '@features/feed/types';
import UserVotePositionControl from './UserVotePositionControl';
import { getVoteSubjectForItem } from '../utils/voteSubjects';

type Props = {
  item: FeedItem;
  compact?: boolean;
};

const VotePromptForFeedItem = ({ item, compact = true }: Props) => {
  const subject = getVoteSubjectForItem(item);
  if (!subject) return null;
  return <UserVotePositionControl subject={subject} compact={compact} showPrompt={false} />;
};

export default VotePromptForFeedItem;
