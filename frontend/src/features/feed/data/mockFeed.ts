import { FeedItem } from '../types';

export const mockFeed: FeedItem[] = [
  {
    id: 1,
    headline: 'House records roll-call vote on Civic Data Transparency Act',
    summary: 'Members voted on final passage with official roll-call totals and member positions available.',
    published_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    branch: 'house',
    source: 'congress.gov',
    url: 'https://clerk.house.gov/Votes/202642',
    tags: ['vote', 'Technology'],
    card_type: 'vote',
    rank_context: {
      score: 98,
      factors: {
        source_freshness: 30,
        lifecycle_importance: 35,
        local_relevance: 22,
        followed_object_relevance: 3,
        source_transparency: 8
      },
      reasons: ['Roll-call votes are high-importance primary-source events.', 'Official source links are available on the card.']
    },
    source_trail_status: 'available',
    source_trail: [
      {
        label: 'House Clerk roll call',
        source: 'house.gov',
        url: 'https://clerk.house.gov/Votes/202642',
        supports: ['vote result', 'member positions']
      }
    ],
    detail: {
      vote: {
        canonical_id: 'vote-house-119-2-42',
        chamber: 'House',
        congress: 119,
        session: '2',
        roll_number: '42',
        vote_date: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
        question: 'On Passage',
        result: 'Passed',
        margin: '10',
        totals: { yea: 220, nay: 210 },
        party_split: { D: { yea: 200 }, R: { nay: 190 } },
        positions: [
          { member_identifier: 'R000037', member_name: 'CA 37 Representative', party: 'D', state: 'CA', district: '37', position: 'yea' },
          { member_identifier: 'T000001', member_name: 'Texas Example Member', party: 'R', state: 'TX', district: '12', position: 'nay' }
        ],
        local_representative_positions: [
          { member_identifier: 'R000037', member_name: 'CA 37 Representative', party: 'D', state: 'CA', district: '37', position: 'yea' }
        ],
        linked_bill: { display_number: 'HR 1234', title: 'Civic Data Transparency Act' },
        source_url: 'https://clerk.house.gov/Votes/202642',
        unavailable: {}
      }
    }
  },
  {
    id: 2,
    headline: 'House Oversight schedules civic data access hearing',
    summary: 'The committee posted a hearing notice with schedule, jurisdiction, and source-backed availability states.',
    published_at: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    event_date: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
    branch: 'house',
    source: 'congress.gov',
    url: 'https://www.congress.gov/event/119th-congress/house-event/116500',
    tags: ['hearing', 'oversight'],
    card_type: 'hearing',
    source_trail_status: 'available',
    source_trail: [
      {
        label: 'Congress.gov hearing',
        source: 'congress.gov',
        url: 'https://www.congress.gov/event/119th-congress/house-event/116500',
        supports: ['hearing schedule']
      }
    ],
    detail: {
      hearing: {
        canonical_id: 'hearing-119-house-116500',
        event_id: '116500',
        congress: 119,
        chamber: 'House',
        title: 'Oversight hearing on civic data access',
        meeting_type: 'Hearing',
        status: 'Scheduled',
        scheduled_at: new Date(Date.now() + 2 * 24 * 60 * 60 * 1000).toISOString(),
        location: 'Rayburn 2154',
        committee: {
          committee_code: 'hsgo',
          name: 'House Oversight and Accountability',
          jurisdiction: 'Government operations oversight.'
        },
        witnesses: [],
        related_bills: [{ display_number: 'HR 1234', title: 'Civic Data Transparency Act' }],
        videos: [],
        transcripts: [],
        source_url: 'https://www.congress.gov/event/119th-congress/house-event/116500',
        follow_supported: true,
        alert_affordance: 'Follow this committee for hearing alerts.',
        unavailable: {
          witnesses: 'Official witness details are not published yet.',
          videos: 'Official video is not published yet.',
          transcripts: 'Official transcript is not published yet.'
        }
      }
    }
  },
  {
    id: 3,
    headline: 'House passes Civic Data Transparency Act',
    summary: 'The bill detail includes lifecycle status, committees, text versions, related votes, and official source trail.',
    published_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    branch: 'house',
    source: 'congress.gov',
    url: 'https://www.congress.gov/bill/119th-congress/house-bill/1234',
    tags: ['bill', 'lifecycle'],
    card_type: 'bill',
    source_trail_status: 'available',
    source_trail: [
      {
        label: 'Congress.gov bill',
        source: 'congress.gov',
        url: 'https://www.congress.gov/bill/119th-congress/house-bill/1234',
        supports: ['bill']
      },
      {
        label: 'CBO cost estimate',
        source: 'cbo',
        url: 'https://www.cbo.gov/publication/12345',
        supports: ['money_context', 'cbo_cost_estimate'],
        confidence: 'direct_source',
        source_category: 'official'
      }
    ],
    money_context_status: 'available',
    money_context_note: 'Money context is source-backed context only; it does not imply corruption, motive, or intent.',
    money_context: [
      {
        label: 'CBO cost estimate',
        value: 'CBO published a cost estimate for this bill.',
        source_relationship: 'direct_source',
        confidence_label: {
          relationship: 'direct_source',
          label: 'Direct source match',
          description: 'The source directly names this bill, member, committee, or record.'
        },
        source_indexes: [1],
        note: 'Money context is source-backed context only; it does not imply corruption, motive, or intent.',
        source_system: 'cbo',
        source_category: 'official'
      }
    ],
    detail: {
      bill: {
        canonical_id: '119-hr-1234',
        display_number: 'HR 1234',
        title: 'Civic Data Transparency Act',
        short_title: 'Civic Data Transparency Act',
        status: 'Passed House.',
        origin_chamber: 'House',
        policy_area: 'Government Operations and Politics',
        introduced_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
        latest_action_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
        sponsors: [{ name: 'Example Sponsor' }],
        cosponsors: [{ name: 'Example Cosponsor' }],
        committees: [{ committee_code: 'hsgo', name: 'House Oversight and Accountability' }],
        timeline: [
          {
            id: 1,
            action_type: 'Passed House',
            text: 'Passed/agreed to in House.',
            acted_at: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
            chamber: 'House',
            source_url: 'https://www.congress.gov/bill/119th-congress/house-bill/1234/actions'
          }
        ],
        text_versions: [{ version_name: 'Introduced in House', source_url: 'https://www.congress.gov/bill/119th-congress/house-bill/1234/text' }],
        amendments: [],
        related_bills: [],
        cbo_cost_estimates: [
          {
            title: 'CBO cost estimate',
            source_url: 'https://www.cbo.gov/publication/12345',
            summary: 'CBO published a cost estimate for this bill.'
          }
        ],
        crs_reports: [],
        votes: [{
          canonical_id: 'vote-house-119-2-42',
          chamber: 'House',
          roll_number: '42',
          question: 'On Passage',
          result: 'Passed',
          source_url: 'https://clerk.house.gov/Votes/202642',
          positions: [
            { member_identifier: 'R000037', member_name: 'CA 37 Representative', party: 'D', state: 'CA', district: '37', position: 'yea' },
            { member_identifier: 'T000001', member_name: 'Texas Example Member', party: 'R', state: 'TX', district: '12', position: 'nay' }
          ],
          local_representative_positions: [
            { member_identifier: 'R000037', member_name: 'CA 37 Representative', party: 'D', state: 'CA', district: '37', position: 'yea' }
          ]
        }],
        vote_eligible: true,
        money_context_status: 'available',
        money_context_note: 'Money context is source-backed context only; it does not imply corruption, motive, or intent.',
        money_context: [
          {
            label: 'CBO cost estimate',
            value: 'CBO published a cost estimate for this bill.',
            source_relationship: 'direct_source',
            source_indexes: [1],
            note: 'Money context is source-backed context only; it does not imply corruption, motive, or intent.',
            source_system: 'cbo',
            source_category: 'official'
          }
        ],
        user_position_prompt: 'Record a personal position for comparison. This is civic tracking, not an official congressional vote.',
        source_url: 'https://www.congress.gov/bill/119th-congress/house-bill/1234',
        unavailable: {
          amendments: 'No official amendments are published yet.'
        }
      }
    }
  },
  {
    id: 4,
    headline: 'Money context unavailable for newly filed disclosure topic',
    summary: 'The feed can show a clear unavailable state when no official money source has been attached yet.',
    published_at: new Date(Date.now() - 7 * 60 * 60 * 1000).toISOString(),
    branch: 'legislative',
    source: 'money-context',
    tags: ['money', 'disclosure'],
    card_type: 'money',
    source_trail_status: 'pending',
    source_trail_note: 'No FEC, LDA, USAspending, disclosure, or CBO source link is attached yet.',
    source_trail: [],
    money_context_status: 'unavailable',
    money_context_note: 'No sourced money context is attached for this card yet.',
    money_context: [
      {
        label: 'Campaign and lobbying context',
        source_relationship: 'unavailable',
        source_indexes: [],
        unavailable_reason: 'No official FEC/OpenFEC or LDA source has been attached.',
        note: 'Money context is source-backed context only; it does not imply corruption, motive, or intent.',
        source_category: 'unavailable'
      }
    ]
  }
];
