import React, { createContext, useContext, useMemo } from 'react';

type CardSkin = 'none' | 'bordered' | 'shadow';

type ThemeContextValue = {
  cardSkin: CardSkin;
};

const ThemeCtx = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children, cardSkin = 'bordered' }: { children: React.ReactNode; cardSkin?: CardSkin }) {
  const value = useMemo(() => ({ cardSkin }), [cardSkin]);
  return <ThemeCtx.Provider value={value}>{children}</ThemeCtx.Provider>;
}

export function useThemeContext() {
  const ctx = useContext(ThemeCtx);
  if (!ctx) {
    // Provide a safe default to avoid runtime crashes in areas that don't need it
    return { cardSkin: 'bordered' } satisfies ThemeContextValue;
  }
  return ctx;
}

