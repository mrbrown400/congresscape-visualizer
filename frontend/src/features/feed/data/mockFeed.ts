import { FeedItem } from '../types';

export const mockFeed: FeedItem[] = [
  {
    id: 1,
    headline: 'Senate passes bipartisan technology modernization bill',
    summary: 'The Senate approved sweeping upgrades for federal technology infrastructure to strengthen cybersecurity and AI readiness.',
    published_at: new Date().toISOString(),
    branch: 'senate',
    source: 'congress.gov',
    url: 'https://www.congress.gov/bill',
    tags: ['Technology', 'Cybersecurity']
  },
  {
    id: 2,
    headline: 'Supreme Court schedules emergency hearing on data privacy case',
    summary: 'Justices fast-track arguments on a case that could reshape digital privacy protections for Americans.',
    published_at: new Date().toISOString(),
    branch: 'judicial',
    source: 'supremecourt.gov',
    tags: ['Privacy', 'Courts']
  },
  {
    id: 3,
    headline: 'EPA announces urgent air quality rule for Western states',
    summary: 'The EPA issued an emergency rule targeting wildfire-induced pollution, coordinating with regional agencies for rapid response.',
    published_at: new Date().toISOString(),
    branch: 'executive',
    source: 'epa.gov',
    tags: ['Environment', 'Urgent']
  }
];
