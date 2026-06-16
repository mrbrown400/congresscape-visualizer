import React, { useMemo, useState } from 'react';
import {
  Linking,
  Pressable,
  ScrollView,
  Share,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { NativeStackScreenProps } from '@react-navigation/native-stack';

import {
  BillDetail,
  Branch,
  CivicMoneyContextItem,
  FeedItem,
  HearingDetail,
  MoneyContextStatus,
  MoneySourceRelationship,
  SourceTrailItem,
  VoteDetail,
  VotePosition,
} from '@features/feed/types';
import BillStatusTracker from '@features/updateDetail/components/BillStatusTracker';
import { useSavedItems } from '@context/SavedItemsContext';
import { useUserPreferences } from '@context/UserPreferencesContext';
import UserVotePositionControl from '@features/votes/components/UserVotePositionControl';
import VoteComparisonPanel from '@features/votes/components/VoteComparisonPanel';
import { VoteSubject, getVoteSubjectForBill, getVoteSubjectForVote } from '@features/votes/utils/voteSubjects';
import { RootStackParamList } from '@navigation/RootNavigator';
import { useTheme } from '@theme/ThemeProvider';
import dayjs from '@utils/dayjs';

type Props = NativeStackScreenProps<RootStackParamList, 'UpdateDetail'>;

const UpdateDetailScreen = ({ route, navigation }: Props) => {
  const { item } = route.params;
  const { neutral, branch: branchColors } = useTheme();
  const { isSaved, toggleSave } = useSavedItems();
  const [voteSearch, setVoteSearch] = useState('');
  const saved = isSaved(item.id);
  const branchColor = branchColors[item.branch as Branch] || branchColors.legislative;

  const handleShare = async () => {
    await Share.share({
      message: `${item.headline}\n\n${item.summary ?? ''}${item.url ? `\n\nSource: ${item.url}` : ''}`,
      title: item.headline,
    });
  };

  return (
    <View style={[styles.container, { backgroundColor: neutral.background }]}>
      <View style={[styles.header, { borderBottomColor: neutral.divider }]}>
        <Pressable style={styles.iconButton} onPress={() => navigation.goBack()} hitSlop={12}>
          <Ionicons name="arrow-back" size={24} color={neutral.textPrimary} />
        </Pressable>
        <View style={styles.headerActions}>
          <Pressable style={styles.iconButton} onPress={() => toggleSave(item)} hitSlop={8}>
            <Ionicons
              name={saved ? 'bookmark' : 'bookmark-outline'}
              size={23}
              color={saved ? branchColors.agency : neutral.textPrimary}
            />
          </Pressable>
          <Pressable style={styles.iconButton} onPress={handleShare} hitSlop={8}>
            <Ionicons name="share-outline" size={23} color={neutral.textPrimary} />
          </Pressable>
        </View>
      </View>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        <View style={styles.kickerRow}>
          <View style={[styles.kicker, { borderColor: branchColor }]}>
            <Text style={[styles.kickerText, { color: branchColor }]}>
              {(item.card_type ?? item.branch).toUpperCase()}
            </Text>
          </View>
          <Text style={[styles.dateText, { color: neutral.textMuted }]}>
            {dayjs(item.published_at).format('MMM D, YYYY h:mm A')}
          </Text>
        </View>

        <Text style={[styles.headline, { color: neutral.textPrimary }]}>{item.headline}</Text>
        <Text style={[styles.summary, { color: neutral.textSecondary }]}>
          {item.summary ?? 'Official summary has not been published yet.'}
        </Text>

        <RankContext item={item} />
        <SourceTrail sources={item.source_trail ?? []} note={item.source_trail_note} />
        <MoneyContextSection
          status={item.money_context_status ?? item.detail?.bill?.money_context_status}
          note={item.money_context_note ?? item.detail?.bill?.money_context_note}
          items={item.money_context ?? item.detail?.bill?.money_context ?? []}
          sources={item.source_trail ?? []}
        />

        {item.detail?.bill ? (
          <BillDetailView item={item} bill={item.detail.bill} />
        ) : item.detail?.vote ? (
          <VoteDetailView vote={item.detail.vote} search={voteSearch} onSearchChange={setVoteSearch} />
        ) : item.detail?.hearing ? (
          <HearingDetailView hearing={item.detail.hearing} />
        ) : (
          <GenericDetail item={item} />
        )}
      </ScrollView>
    </View>
  );
};

const BillDetailView = ({ item, bill }: { item: FeedItem; bill: BillDetail }) => {
  const { neutral, branch } = useTheme();
  const {
    preferences,
    followBill,
    unfollowBill,
  } = useUserPreferences();
  const followed = preferences.followedBills.includes(bill.canonical_id);
  const statusStep = billStatusStep(bill.status);
  const voteSubject = getVoteSubjectForBill(bill);

  return (
    <View style={styles.detailStack}>
      <ActionRow
        primaryLabel={followed ? 'Following Bill' : 'Follow Bill'}
        onPrimary={() => followed ? unfollowBill(bill.canonical_id) : followBill(bill.canonical_id)}
        sourceUrl={bill.source_url ?? item.url}
      />

      <Section title="Status">
        <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>{bill.status}</Text>
        <BillStatusTracker currentStep={statusStep} />
      </Section>

      {voteSubject && (
        <Section title="Your Position">
          <UserVotePositionControl subject={voteSubject} />
        </Section>
      )}

      {voteSubject && <BillVoteComparisons votes={bill.votes} subject={voteSubject} />}

      <RecordList title="Sponsors" records={bill.sponsors} emptyText="Official sponsor data is not published yet." />
      <RecordList title="Cosponsors" records={bill.cosponsors} emptyText="Official cosponsor data is not published yet." />
      <RecordList title="Committees" records={bill.committees} emptyText={bill.unavailable.committees ?? 'No committees are linked.'} />
      <Section title="Lifecycle">
        {bill.timeline.length === 0 ? (
          <Unavailable text="No official lifecycle actions are published yet." />
        ) : (
          bill.timeline.map(action => (
            <View key={action.id} style={[styles.timelineRow, { borderLeftColor: branch.legislative }]}>
              <Text style={[styles.metaText, { color: neutral.textMuted }]}>
                {action.acted_at ? dayjs(action.acted_at).format('MMM D, YYYY') : 'Date unavailable'}
              </Text>
              <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{action.text}</Text>
              {action.source_url && <SourceLink url={action.source_url} label="Official action" />}
            </View>
          ))
        )}
      </Section>
      <RecordList title="Text Versions" records={bill.text_versions} emptyText={bill.unavailable.text_versions ?? 'No official text versions are published yet.'} />
      <RecordList title="Amendments" records={bill.amendments} emptyText="No official amendments are published yet." />
      <RecordList title="Votes" records={bill.votes} emptyText={bill.unavailable.votes ?? 'No votes are linked yet.'} />
      <RecordList title="CBO And CRS" records={[...bill.cbo_cost_estimates, ...bill.crs_reports]} emptyText="No CBO estimate or CRS report is published yet." />
      <RecordList title="Related Bills" records={bill.related_bills} emptyText="No related bills are published yet." />
    </View>
  );
};

const VoteDetailView = ({
  vote,
  search,
  onSearchChange,
}: {
  vote: VoteDetail;
  search: string;
  onSearchChange: (value: string) => void;
}) => {
  const { neutral, branch } = useTheme();
  const voteSubject = getVoteSubjectForVote(vote);
  const filteredPositions = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return vote.positions;
    return vote.positions.filter(position => (
      position.member_name.toLowerCase().includes(query) ||
      (position.party ?? '').toLowerCase().includes(query) ||
      position.position.toLowerCase().includes(query) ||
      (position.state ?? '').toLowerCase().includes(query)
    ));
  }, [search, vote.positions]);

  return (
    <View style={styles.detailStack}>
      <ActionRow sourceUrl={vote.source_url} />
      <Section title="Your Position">
        <UserVotePositionControl subject={voteSubject} />
      </Section>
      <VoteComparisonPanel
        subject={voteSubject}
        positions={vote.positions}
        localPositions={vote.local_representative_positions}
      />
      <Section title="Roll Call">
        <FactGrid facts={[
          ['Chamber', vote.chamber],
          ['Roll', vote.roll_number],
          ['Result', vote.result ?? 'Unavailable'],
          ['Margin', vote.margin ?? 'Unavailable'],
        ]} />
        <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{vote.question}</Text>
      </Section>

      <Section title="Totals">
        <RecordPills values={vote.totals} />
      </Section>

      <Section title="Party Split">
        <RecordPills values={vote.party_split} />
      </Section>

      <Section title="Local Representatives">
        {vote.local_representative_positions.length === 0 ? (
          <Unavailable text={vote.unavailable.local_representatives ?? 'No local representative match is available.'} />
        ) : (
          vote.local_representative_positions.map(position => (
            <PositionRow key={position.member_identifier} position={position} highlight />
          ))
        )}
      </Section>

      {vote.linked_bill && (
        <Section title="Linked Bill">
          <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>
            {recordLabel(vote.linked_bill)}
          </Text>
        </Section>
      )}

      <Section title="Member Positions">
        <TextInput
          value={search}
          onChangeText={onSearchChange}
          placeholder="Search by member, party, state, or position"
          placeholderTextColor={neutral.textMuted}
          style={[styles.searchInput, { color: neutral.textPrimary, borderColor: neutral.divider }]}
        />
        {filteredPositions.length === 0 ? (
          <Unavailable text={vote.unavailable.member_positions ?? 'No matching positions.'} />
        ) : (
          filteredPositions.slice(0, 80).map(position => (
            <PositionRow key={position.member_identifier} position={position} />
          ))
        )}
        {filteredPositions.length > 80 && (
          <Text style={[styles.metaText, { color: branch.agency }]}>
            Showing first 80 matching positions.
          </Text>
        )}
      </Section>
    </View>
  );
};

const BillVoteComparisons = ({ votes, subject }: { votes: Record<string, unknown>[]; subject: VoteSubject }) => {
  const comparableVotes = votes.filter(vote => getVotePositions(vote, 'positions').length > 0);
  if (comparableVotes.length === 0) return null;

  return (
    <>
      {comparableVotes.map(vote => {
        const voteId = getRecordString(vote, 'canonical_id') ?? subject.voteId ?? subject.subjectId;
        const rollNumber = getRecordString(vote, 'roll_number');
        const voteSubject = {
          ...subject,
          voteId,
          sourceUrl: getRecordString(vote, 'source_url') ?? subject.sourceUrl,
          label: rollNumber ? `${subject.label} roll ${rollNumber}` : subject.label,
        };
        return (
          <VoteComparisonPanel
            key={voteId}
            subject={voteSubject}
            title={rollNumber ? `Roll Call ${rollNumber} Comparison` : 'Vote Comparison'}
            positions={getVotePositions(vote, 'positions')}
            localPositions={getVotePositions(vote, 'local_representative_positions')}
          />
        );
      })}
    </>
  );
};

const HearingDetailView = ({ hearing }: { hearing: HearingDetail }) => {
  const { neutral, branch } = useTheme();
  const { preferences, followCommittee, unfollowCommittee } = useUserPreferences();
  const committeeCode = getRecordString(hearing.committee, 'committee_code');
  const committeeName = getRecordString(hearing.committee, 'name');
  const followed = committeeCode ? preferences.followedCommittees.includes(committeeCode) : false;

  return (
    <View style={styles.detailStack}>
      <ActionRow
        primaryLabel={committeeCode ? (followed ? 'Following Committee' : 'Follow Committee') : undefined}
        onPrimary={committeeCode ? () => followed ? unfollowCommittee(committeeCode) : followCommittee(committeeCode) : undefined}
        sourceUrl={hearing.source_url}
      />
      <Section title="Schedule">
        <FactGrid facts={[
          ['Status', hearing.status ?? 'Unavailable'],
          ['Type', hearing.meeting_type ?? 'Unavailable'],
          ['When', hearing.scheduled_at ? dayjs(hearing.scheduled_at).format('MMM D, YYYY h:mm A') : 'Unavailable'],
          ['Location', hearing.location ?? 'Unavailable'],
        ]} />
      </Section>
      <Section title="Committee">
        {committeeName ? (
          <>
            <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{committeeName}</Text>
            {getRecordString(hearing.committee, 'jurisdiction') && (
              <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>
                {getRecordString(hearing.committee, 'jurisdiction')}
              </Text>
            )}
          </>
        ) : (
          <Unavailable text="Official committee details are not published yet." />
        )}
      </Section>
      <RecordList title="Witnesses" records={hearing.witnesses} emptyText={hearing.unavailable.witnesses ?? 'Witnesses are not published yet.'} />
      <RecordList title="Related Bills" records={hearing.related_bills} emptyText="No related bills are published yet." />
      <RecordList title="Video" records={hearing.videos} emptyText={hearing.unavailable.videos ?? 'Official video is not published yet.'} />
      <RecordList title="Transcript" records={hearing.transcripts} emptyText={hearing.unavailable.transcripts ?? 'Official transcript is not published yet.'} />
      {hearing.alert_affordance && (
        <View style={[styles.notice, { borderColor: branch.agency }]}>
          <Ionicons name="notifications-outline" size={18} color={branch.agency} />
          <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>{hearing.alert_affordance}</Text>
        </View>
      )}
    </View>
  );
};

const GenericDetail = ({ item }: { item: FeedItem }) => {
  const { neutral } = useTheme();
  return (
    <View style={styles.detailStack}>
      <Section title="Summary">
        <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>
          {item.full_text ?? item.summary ?? 'No additional detail is available yet.'}
        </Text>
      </Section>
      {item.url && <ActionRow sourceUrl={item.url} />}
    </View>
  );
};

const RankContext = ({ item }: { item: FeedItem }) => {
  const { neutral } = useTheme();
  const factors = item.rank_context?.factors;
  if (!factors) return null;
  return (
    <Section title="Why This Is Ranked Here">
      <View style={styles.factorGrid}>
        {Object.entries(factors).map(([key, value]) => (
          <View key={key} style={[styles.factor, { borderColor: neutral.divider }]}>
            <Text style={[styles.factorLabel, { color: neutral.textMuted }]}>{key.replace(/_/g, ' ')}</Text>
            <Text style={[styles.factorValue, { color: neutral.textPrimary }]}>{Math.round(value)}</Text>
          </View>
        ))}
      </View>
    </Section>
  );
};

const SourceTrail = ({ sources, note }: { sources: SourceTrailItem[]; note?: string | null }) => (
  <Section title="Source Trail">
    {sources.length === 0 ? (
      <Unavailable text={note ?? 'Official sources are not attached yet.'} />
    ) : (
      sources.map(source => (
        <View key={`${source.source}-${source.url}`} style={styles.sourceTrailRow}>
          <SourceLink url={source.url} label={`${source.label} · ${source.source}`} />
          <View style={styles.chipRow}>
            {source.confidence && <RelationshipChip relationship={source.confidence} />}
            {source.source_category && <SourceCategoryChip category={source.source_category} />}
          </View>
        </View>
      ))
    )}
  </Section>
);

const MoneyContextSection = ({
  status,
  note,
  items,
  sources,
}: {
  status?: MoneyContextStatus;
  note?: string | null;
  items: CivicMoneyContextItem[];
  sources: SourceTrailItem[];
}) => {
  if ((!status || status === 'not_applicable') && items.length === 0) return null;

  return (
    <Section title="Money Context">
      {note && <Unavailable text={note} />}
      {items.length === 0 ? (
        <Unavailable text="No sourced money context is attached yet." />
      ) : (
        items.map((item, index) => (
          <MoneyContextRow key={`${item.label}-${index}`} item={item} sources={sources} />
        ))
      )}
    </Section>
  );
};

const MoneyContextRow = ({
  item,
  sources,
}: {
  item: CivicMoneyContextItem;
  sources: SourceTrailItem[];
}) => {
  const { neutral } = useTheme();
  const linkedSources = item.source_indexes
    .map(index => sources[index])
    .filter((source): source is SourceTrailItem => Boolean(source));

  return (
    <View style={[styles.recordRow, { borderColor: neutral.divider }]}>
      <View style={styles.moneyHeader}>
        <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{item.label}</Text>
        <RelationshipChip relationship={item.source_relationship} />
      </View>
      {item.value && (
        <Text style={[styles.bodyText, { color: neutral.textSecondary }]}>{item.value}</Text>
      )}
      {item.confidence_label?.description && (
        <Text style={[styles.metaText, { color: neutral.textMuted }]}>
          {item.confidence_label.description}
        </Text>
      )}
      {item.unavailable_reason && (
        <Unavailable text={item.unavailable_reason} />
      )}
      {item.note && (
        <Text style={[styles.metaText, { color: neutral.textMuted }]}>{item.note}</Text>
      )}
      {linkedSources.map(source => (
        <SourceLink
          key={`${source.source}-${source.url}`}
          url={source.url}
          label={`${source.label} · ${source.source}`}
        />
      ))}
    </View>
  );
};

const RelationshipChip = ({ relationship }: { relationship: MoneySourceRelationship }) => {
  const { branch, neutral } = useTheme();
  const label = relationshipLabel(relationship);
  const color = relationship === 'unavailable' ? neutral.textMuted : branch.agency;
  return (
    <View style={[styles.relationshipChip, { borderColor: color }]}>
      <Text style={[styles.relationshipChipText, { color }]}>{label}</Text>
    </View>
  );
};

const SourceCategoryChip = ({ category }: { category: string }) => {
  const { neutral } = useTheme();
  return (
    <View style={[styles.sourceCategoryChip, { borderColor: neutral.divider }]}>
      <Text style={[styles.sourceCategoryChipText, { color: neutral.textMuted }]}>
        {category.replace(/_/g, ' ')}
      </Text>
    </View>
  );
};

const Section = ({ title, children }: { title: string; children: React.ReactNode }) => {
  const { neutral } = useTheme();
  return (
    <View style={[styles.section, { borderColor: neutral.divider }]}>
      <Text style={[styles.sectionTitle, { color: neutral.textMuted }]}>{title.toUpperCase()}</Text>
      {children}
    </View>
  );
};

const ActionRow = ({
  primaryLabel,
  onPrimary,
  sourceUrl,
}: {
  primaryLabel?: string;
  onPrimary?: () => void;
  sourceUrl?: string | null;
}) => {
  const { branch } = useTheme();
  if (!primaryLabel && !sourceUrl) return null;
  return (
    <View style={styles.actionRow}>
      {primaryLabel && onPrimary && (
        <Pressable style={[styles.primaryButton, { backgroundColor: branch.agency }]} onPress={onPrimary}>
          <Text style={styles.primaryButtonText}>{primaryLabel}</Text>
        </Pressable>
      )}
      {sourceUrl && (
        <Pressable style={[styles.secondaryButton, { borderColor: branch.agency }]} onPress={() => Linking.openURL(sourceUrl)}>
          <Ionicons name="open-outline" size={18} color={branch.agency} />
          <Text style={[styles.secondaryButtonText, { color: branch.agency }]}>Official Source</Text>
        </Pressable>
      )}
    </View>
  );
};

const SourceLink = ({ url, label }: { url: string; label: string }) => {
  const { branch } = useTheme();
  return (
    <Pressable style={styles.sourceLink} onPress={() => Linking.openURL(url)}>
      <Ionicons name="link-outline" size={17} color={branch.agency} />
      <Text style={[styles.linkText, { color: branch.agency }]}>{label}</Text>
    </Pressable>
  );
};

const RecordList = ({
  title,
  records,
  emptyText,
}: {
  title: string;
  records: Record<string, unknown>[];
  emptyText: string;
}) => (
  <Section title={title}>
    {records.length === 0 ? (
      <Unavailable text={emptyText} />
    ) : (
      records.slice(0, 12).map((record, index) => (
        <RecordRow key={`${title}-${index}`} record={record} />
      ))
    )}
  </Section>
);

const RecordRow = ({ record }: { record: Record<string, unknown> }) => {
  const { neutral } = useTheme();
  return (
    <View style={[styles.recordRow, { borderColor: neutral.divider }]}>
      <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{recordLabel(record)}</Text>
      {recordMeta(record) && (
        <Text style={[styles.metaText, { color: neutral.textMuted }]}>{recordMeta(record)}</Text>
      )}
      {getRecordString(record, 'source_url') && (
        <SourceLink url={getRecordString(record, 'source_url') ?? ''} label="Official link" />
      )}
    </View>
  );
};

const PositionRow = ({ position, highlight = false }: { position: VotePosition; highlight?: boolean }) => {
  const { neutral, branch } = useTheme();
  return (
    <View style={[styles.positionRow, { borderColor: highlight ? branch.agency : neutral.divider }]}>
      <View style={styles.positionTextBlock}>
        <Text style={[styles.bodyTextStrong, { color: neutral.textPrimary }]}>{position.member_name}</Text>
        <Text style={[styles.metaText, { color: neutral.textMuted }]}>
          {[position.party, position.state, position.district ? `District ${position.district}` : null].filter(Boolean).join(' · ')}
        </Text>
      </View>
      <Text style={[styles.voteBadge, { color: branch.agency }]}>{position.position.toUpperCase()}</Text>
    </View>
  );
};

const FactGrid = ({ facts }: { facts: [string, string][] }) => {
  const { neutral } = useTheme();
  return (
    <View style={styles.factGrid}>
      {facts.map(([label, value]) => (
        <View key={label} style={[styles.fact, { borderColor: neutral.divider }]}>
          <Text style={[styles.factorLabel, { color: neutral.textMuted }]}>{label}</Text>
          <Text style={[styles.factValue, { color: neutral.textPrimary }]}>{value}</Text>
        </View>
      ))}
    </View>
  );
};

const RecordPills = ({ values }: { values: Record<string, unknown> }) => {
  const { neutral } = useTheme();
  const entries = Object.entries(values);
  if (entries.length === 0) {
    return <Unavailable text="Official totals are not published yet." />;
  }
  return (
    <View style={styles.pillWrap}>
      {entries.map(([key, value]) => (
        <View key={key} style={[styles.pill, { backgroundColor: neutral.card, borderColor: neutral.divider }]}>
          <Text style={[styles.pillText, { color: neutral.textPrimary }]}>
            {key}: {formatUnknown(value)}
          </Text>
        </View>
      ))}
    </View>
  );
};

const Unavailable = ({ text }: { text: string }) => {
  const { neutral } = useTheme();
  return <Text style={[styles.unavailable, { color: neutral.textMuted }]}>{text}</Text>;
};

const recordLabel = (record: Record<string, unknown>) => {
  return (
    getRecordString(record, 'display_number') ||
    getRecordString(record, 'version_name') ||
    getRecordString(record, 'title') ||
    getRecordString(record, 'name') ||
    getRecordString(record, 'label') ||
    getRecordString(record, 'result') ||
    formatUnknown(record)
  );
};

const recordMeta = (record: Record<string, unknown>) => {
  return (
    getRecordString(record, 'jurisdiction') ||
    getRecordString(record, 'version_code') ||
    getRecordString(record, 'roll_number') ||
    getRecordString(record, 'source') ||
    null
  );
};

const getRecordString = (record: Record<string, unknown> | null | undefined, key: string) => {
  const raw = record?.[key];
  return typeof raw === 'string' ? raw : null;
};

const getVotePositions = (record: Record<string, unknown>, key: string): VotePosition[] => {
  const raw = record[key];
  return Array.isArray(raw) ? raw as VotePosition[] : [];
};

const relationshipLabel = (relationship: MoneySourceRelationship) => {
  switch (relationship) {
    case 'direct_source':
      return 'Direct source';
    case 'related_entity':
      return 'Related entity';
    case 'topic_context':
      return 'Topic context';
    case 'unavailable':
      return 'Unavailable';
    default:
      return 'Unavailable';
  }
};

const formatUnknown = (value: unknown): string => {
  if (value === null || value === undefined) return 'Unavailable';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  if (Array.isArray(value)) return `${value.length} item${value.length === 1 ? '' : 's'}`;
  if (typeof value === 'object') return Object.entries(value).map(([key, child]) => `${key}: ${formatUnknown(child)}`).join(', ');
  return String(value);
};

const billStatusStep = (status: string) => {
  const lower = status.toLowerCase();
  if (lower.includes('law') || lower.includes('signed') || lower.includes('veto')) return 6;
  if (lower.includes('president')) return 5;
  if (lower.includes('conference')) return 4;
  if (lower.includes('senate') || lower.includes('other chamber')) return 3;
  if (lower.includes('passed') || lower.includes('floor')) return 2;
  if (lower.includes('committee')) return 1;
  return 0;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingTop: 50,
    paddingHorizontal: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
  },
  iconButton: {
    padding: 8,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 8,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 120,
    gap: 16,
  },
  kickerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    alignItems: 'center',
  },
  kicker: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  kickerText: {
    fontSize: 12,
    fontWeight: '800',
  },
  dateText: {
    fontSize: 12,
  },
  headline: {
    fontSize: 27,
    fontWeight: '800',
    lineHeight: 34,
  },
  summary: {
    fontSize: 16,
    lineHeight: 24,
  },
  detailStack: {
    gap: 14,
  },
  section: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    gap: 10,
  },
  sectionTitle: {
    fontSize: 12,
    fontWeight: '800',
  },
  bodyText: {
    fontSize: 15,
    lineHeight: 22,
  },
  bodyTextStrong: {
    fontSize: 15,
    lineHeight: 21,
    fontWeight: '700',
  },
  metaText: {
    fontSize: 12,
    lineHeight: 17,
  },
  linkText: {
    flex: 1,
    fontSize: 13,
    fontWeight: '700',
  },
  sourceLink: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  sourceTrailRow: {
    gap: 6,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  moneyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
  },
  relationshipChip: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  relationshipChipText: {
    fontSize: 11,
    fontWeight: '800',
  },
  sourceCategoryChip: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  sourceCategoryChipText: {
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'capitalize',
  },
  actionRow: {
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
  },
  primaryButton: {
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontWeight: '800',
    fontSize: 13,
  },
  secondaryButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  secondaryButtonText: {
    fontWeight: '800',
    fontSize: 13,
  },
  factorGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  factor: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
    minWidth: 110,
    flex: 1,
  },
  factorLabel: {
    fontSize: 11,
    textTransform: 'capitalize',
  },
  factorValue: {
    fontSize: 18,
    fontWeight: '800',
  },
  positionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  positionButton: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 11,
    paddingVertical: 8,
  },
  positionText: {
    fontSize: 13,
    fontWeight: '800',
  },
  timelineRow: {
    borderLeftWidth: 3,
    paddingLeft: 10,
    gap: 4,
  },
  recordRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    gap: 4,
  },
  factGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  fact: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 8,
    minWidth: 130,
    flex: 1,
  },
  factValue: {
    fontSize: 15,
    fontWeight: '800',
  },
  pillWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  pill: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 7,
  },
  pillText: {
    fontSize: 13,
    fontWeight: '700',
  },
  searchInput: {
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
  },
  positionRow: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
  },
  positionTextBlock: {
    flex: 1,
  },
  voteBadge: {
    fontSize: 12,
    fontWeight: '800',
  },
  notice: {
    borderWidth: 1,
    borderRadius: 8,
    padding: 12,
    flexDirection: 'row',
    gap: 8,
    alignItems: 'center',
  },
  unavailable: {
    fontSize: 14,
    lineHeight: 20,
  },
});

export default UpdateDetailScreen;
