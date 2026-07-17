import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const read = (file) => readFile(resolve(root, file), 'utf8');

const contrastRatio = (foreground, background) => {
  const channel = (value) => {
    const normalized = Number.parseInt(value, 16) / 255;
    return normalized <= 0.03928 ? normalized / 12.92 : ((normalized + 0.055) / 1.055) ** 2.4;
  };
  const luminance = (color) => {
    const rgb = color.replace('#', '');
    const channels = [rgb.slice(0, 2), rgb.slice(2, 4), rgb.slice(4, 6)].map(channel);
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  };
  const lighter = Math.max(luminance(foreground), luminance(background));
  const darker = Math.min(luminance(foreground), luminance(background));
  return (lighter + 0.05) / (darker + 0.05);
};

const [tabs, saved, storage, card, colors, types] = await Promise.all([
  read('src/navigation/MainTabNavigator.tsx'),
  read('src/features/saved/screens/SavedScreen.tsx'),
  read('src/context/SavedItemsContext.tsx'),
  read('src/features/feed/components/FeedCard.tsx'),
  read('src/theme/colors.ts'),
  read('src/features/feed/types/index.ts'),
]);

const checks = [
  ['all main tabs expose a button role', ['Today', 'Calendar', 'Explore', 'My LA'].every((label) => tabs.includes(label)) && tabs.includes('accessibilityRole="button"')],
  ['saved data has a clear-all path', storage.includes('AsyncStorage') && storage.includes('clearAll') && saved.includes('onPress={clearAll}')],
  ['feed source states remain visible', card.includes('source_trail_status') && card.includes('Official source trail pending')],
  ['text scaling is not disabled', !tabs.includes('allowFontScaling={false}') && !saved.includes('allowFontScaling={false}')],
  ['public feed types do not expose raw address fields', !types.includes('raw_address') && !types.includes('raw_response')],
  ['neutral text colors meet WCAG AA against the app background', contrastRatio('#071A33', '#F8FAFC') >= 4.5 && contrastRatio('#334155', '#F8FAFC') >= 4.5],
  ['theme defines semantic warning/error states', colors.includes('warning') && colors.includes('error')],
];

const failed = checks.filter(([, passed]) => !passed);
for (const [label, passed] of checks) console.log(`${passed ? 'PASS' : 'FAIL'} ${label}`);
if (failed.length) process.exitCode = 1;
