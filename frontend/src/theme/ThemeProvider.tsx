import React, { PropsWithChildren, createContext, useContext, useMemo } from 'react';
import { StatusBar } from 'expo-status-bar';
import { useColorScheme } from 'react-native';

import { branchPalette, neutralPalette } from './colors';

type Theme = {
  branch: typeof branchPalette;
  neutral: typeof neutralPalette;
  isDark: boolean;
};

const ThemeContext = createContext<Theme | undefined>(undefined);

export const ThemeProvider = ({ children }: PropsWithChildren) => {
  const system = useColorScheme();
  const value = useMemo<Theme>(() => ({
    branch: branchPalette,
    neutral: neutralPalette,
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
