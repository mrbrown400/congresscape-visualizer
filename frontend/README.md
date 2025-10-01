# Congresscape Mobile App

React Native (Expo) client delivering a TikTok-style feed of U.S. government actions across all branches.

## Highlights
- Vertical, card-based feed with branch color-coding
- Top tabs for contextual feeds (For You, Trending, Urgent, House/Senate, Executive, Hearings, Saved)
- Onboarding flow to capture interests for personalization
- API client wired to FastAPI backend with mock fallback data for offline development
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
- `App.tsx` – entry point wrapping navigation + theming
- `src/navigation` – stack + top tab navigators
- `src/features` – feature-oriented screens, hooks, and components
- `src/services` – API wrapper and feed client
- `src/theme` – palette + theming utilities
- `src/components` – shared UI primitives (filter pills, etc.)
- `src/utils` – shared utilities (dayjs configuration)

## Next Steps
- Persist onboarding selections with AsyncStorage and attach to personalization API
- Integrate push notifications for urgent actions
- Add deep-dive “Full Coverage” view that expands to audio/video/link collections
- Share UI primitives with a future web app via React Native Web
