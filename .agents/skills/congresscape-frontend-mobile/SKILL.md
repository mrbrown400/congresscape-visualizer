---
name: congresscape-frontend-mobile
description: Use for Expo/React Native screens, navigation, theme, mobile UX, and frontend TypeScript work.
---

# Congresscape Frontend Mobile

Use this skill for user-facing mobile app work.

## Rules

- Preserve feature-based structure under `frontend/src/features/`.
- Keep navigation types aligned with screen params.
- Keep `frontend/tsconfig.json` path aliases synchronized with `frontend/babel.config.js`.
- Use branch-aware colors from `frontend/src/theme/` instead of hard-coded palettes where practical.
- Keep API calls in `frontend/src/services/` and hooks/features focused on presentation state.
- For Expo web smoke checks, set `EXPO_PUBLIC_API_BASE_URL` when testing against the local backend.

## Common Owners

- App root: `frontend/App.tsx`
- Navigation: `frontend/src/navigation/`
- Theme: `frontend/src/theme/`
- API clients: `frontend/src/services/`
- Shared components: `frontend/src/components/`
- Feature screens: `frontend/src/features/`
- Context: `frontend/src/context/`

## Verification

```bash
cd frontend && npx tsc --noEmit
cd frontend && npm run lint
```

Browser-facing changes should also get an Expo web or Browser smoke check when the dependency set can start cleanly.
