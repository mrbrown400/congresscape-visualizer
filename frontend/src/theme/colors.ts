export const branchPalette = {
  legislative: '#1D4ED8',
  house: '#2563EB',
  senate: '#1E40AF',
  judicial: '#7C3AED',
  executive: '#10B981',
  agency: '#F59E0B',
  urgent: '#EF4444'
};

export const neutralPalette = {
  background: '#040C1A',
  surface: '#0B1D3A',
  card: '#12294F',
  cardHover: '#1A3562',
  textPrimary: '#F8FAFC',
  textSecondary: '#C7D2FE',
  textMuted: '#94A3B8',
  divider: '#1F3A68',
  border: '#334155'
};

// Semantic colors for status and urgency
export const semanticPalette = {
  // Urgency levels
  urgent: '#EF4444',
  important: '#F59E0B',
  normal: '#6B7280',

  // Status indicators
  passed: '#10B981',
  pending: '#F59E0B',
  failed: '#EF4444',
  active: '#3B82F6',

  // UI feedback
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6'
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
    letterSpacing: 0.5,
  },
  overline: {
    fontSize: 12,
    fontWeight: '600' as const,
    lineHeight: 16,
    letterSpacing: 1.5,
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
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
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
