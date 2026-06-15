import React, { PropsWithChildren, createContext, useContext, useMemo } from 'react';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';

import {
  branchPalette,
  neutralPalette,
  semanticPalette,
  typography,
  spacing,
  borderRadius
} from './colors';

type Theme = {
  branch: typeof branchPalette;
  neutral: typeof neutralPalette;
  semantic: typeof semanticPalette;
  typography: typeof typography;
  spacing: typeof spacing;
  borderRadius: typeof borderRadius;
  isDark: boolean;
};

const ThemeContext = createContext<Theme | undefined>(undefined);

export const ThemeProvider = ({ children }: PropsWithChildren) => {
  const system = useColorScheme();
  const value = useMemo<Theme>(() => ({
    branch: branchPalette,
    neutral: neutralPalette,
    semantic: semanticPalette,
    typography,
    spacing,
    borderRadius,
    isDark: true // Default to dark mode aesthetic
  }), [system]);

  return (
    <ThemeContext.Provider value={value}>
      <StatusBar style="light" />
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return ctx;
};
