# Congresscape Mobile App

React Native (Expo) client that surfaces a single daily briefing with highlights, deep dives, and push alerts when new briefings drop.

## Highlights
- Narrative “Daily Briefing” screen with highlight bullets and deep-dive cards
- Push notification opt-in using Expo notifications so users get pinged only when there’s a new summary
- Onboarding flow to capture interests for future personalization
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
- `src/navigation` – stack navigator routing between onboarding and the briefing
- `src/features/dailyBrief` – hooks, types, and UI for the daily summary experience
- `src/services` – API wrapper plus daily brief + notification clients
- `src/theme` – palette + theming utilities
- `src/components` – shared UI primitives
- `src/utils` – shared utilities (dayjs configuration)

## Next Steps
- Persist onboarding selections with AsyncStorage and attach to personalization API
- Tighten push notification copy and include branch/topic filters once preferences land
- Add deep-dive “Full Coverage” view that expands to audio/video/link collections
- Share UI primitives with a future web app via React Native Web
