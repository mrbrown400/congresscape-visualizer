export const branchPalette = {
  legislative: '#1D4ED8',
  house: '#2563EB',
  senate: '#123A70',
  judicial: '#475569',
  executive: '#047857',
  agency: '#1D4ED8',
  urgent: '#DC2626'
};

export const neutralPalette = {
  background: '#F8FAFC',
  surface: '#FFFFFF',
  card: '#FFFFFF',
  cardHover: '#F1F5F9',
  textPrimary: '#071A33',
  textSecondary: '#334155',
  textMuted: '#64748B',
  divider: '#E2E8F0',
  border: '#CBD5E1'
};

// Semantic colors for status and urgency
export const semanticPalette = {
  // Urgency levels
  urgent: '#EF4444',
  important: '#B45309',
  normal: '#6B7280',

  // Status indicators
  passed: '#047857',
  pending: '#B45309',
  failed: '#DC2626',
  active: '#1D4ED8',

  // UI feedback
  success: '#047857',
  warning: '#B45309',
  error: '#DC2626',
  info: '#1D4ED8'
};

// Typography scale
export const typography = {
  displayLarge: {
    fontSize: 32,
    fontWeight: '800' as const,
    lineHeight: 40,
  },
  displayMedium: {
    fontSize: 24,
    fontWeight: '700' as const,
    lineHeight: 32,
  },
  headline: {
    fontSize: 20,
    fontWeight: '600' as const,
    lineHeight: 28,
  },
  titleLarge: {
    fontSize: 18,
    fontWeight: '600' as const,
    lineHeight: 26,
  },
  titleMedium: {
    fontSize: 16,
    fontWeight: '600' as const,
    lineHeight: 24,
  },
  body: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 24,
  },
  bodySmall: {
    fontSize: 14,
    fontWeight: '400' as const,
    lineHeight: 20,
  },
  caption: {
    fontSize: 12,
    fontWeight: '500' as const,
    lineHeight: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600' as const,
    lineHeight: 20,
    letterSpacing: 0,
  },
  overline: {
    fontSize: 12,
    fontWeight: '600' as const,
    lineHeight: 16,
    letterSpacing: 0,
  }
};

// Spacing scale
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

// Border radius scale
export const borderRadius = {
  sm: 4,
  md: 6,
  lg: 8,
  xl: 8,
  full: 999,
};

// Branch icons mapping (for use with icon libraries)
export const branchIcons = {
  legislative: 'bank',
  house: 'bank',
  senate: 'bank',
  judicial: 'scale-balance',
  executive: 'file-document',
  agency: 'office-building',
};
