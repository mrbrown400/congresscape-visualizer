---
name: congresscape-browser-verification
description: Use for Expo web and Browser smoke checks of Congresscape frontend behavior.
---

# Congresscape Browser Verification

Use this skill when frontend changes affect visible behavior, navigation, loading/error states, or API integration.

## Setup

Run the backend when the frontend needs live data:

```bash
cd backend && poetry run uvicorn app.main:app --reload
```

Run Expo web with the local API URL:

```bash
cd frontend && EXPO_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1 npm run web
```

## Expectations

- Check the first visible screen, navigation, loading/error states, and at least one API-backed path.
- Capture the exact blocker if Expo web cannot start due dependency mismatches.
- Prefer deterministic local data or seeded SQLite for smoke checks.
- Do not treat device-only push notification behavior as verified by a browser check.

## Closeout

Report the URL tested, screen or flow checked, console errors if any, and screenshots when useful.
