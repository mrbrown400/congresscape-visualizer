# Congresscape Mobile App

React Native (Expo) client for a primary-source civic feed. The app is shaped around sourced cards for Today, My Government, Bills, Votes, Hearings, Money, and Alerts instead of political social media posts.

## Highlights
- Today-first feed surfaces for source-backed government activity
- Shared civic card types for what happened, why it matters, involved entities, money context, and source trail
- Push notification opt-in using Expo notifications for future alerts when bills move, representatives vote, hearings are scheduled, or official text changes
- Onboarding flow to capture interests and followed objects for future personalization
- API client wired to FastAPI backend with graceful fallback copy when the network is down
- Modular architecture ready for web support via Expo

## Getting Started

```bash
cd frontend
npm install
npm run start
```

Set the API base URL (optional) in `app.config` or via environment variable when launching:

```bash
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run start
```

## Structure
- `App.tsx` – entry point wrapping navigation, theming, and push registration hook
- `src/navigation` – stack navigator routing between onboarding and civic feed surfaces
- `src/features/dailyBrief` – compatibility hooks, types, and UI for the current summary experience
- `src/features/feed` – feed UI and shared civic card/feed types
- `src/services` – API wrapper plus feed, summary, update, and notification clients
- `src/theme` – palette + theming utilities
- `src/components` – shared UI primitives
- `src/utils` – shared utilities (dayjs configuration)

## Next Steps
- Persist followed bills, members, committees, topics, and district context with AsyncStorage
- Add source trail and money context affordances to feed/detail cards
- Add user bill-position prompts and representative comparison once canonical vote data lands
- Add deep-dive views for bill lifecycle, votes, hearings, and money context
- Share UI primitives with a future web app via React Native Web
