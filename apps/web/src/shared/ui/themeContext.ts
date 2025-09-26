import { createContext, useContext } from 'react';

type CardSkin = 'none' | 'bordered' | 'shadow';

type ThemeContextValue = {
  cardSkin: CardSkin;
};

const ThemeCtx = createContext<ThemeContextValue | null>(null);

const useThemeContext = (): ThemeContextValue => {
  const ctx = useContext(ThemeCtx);
  if (!ctx) {
    return { cardSkin: 'bordered' } satisfies ThemeContextValue;
  }
  return ctx;
};

export { ThemeCtx, useThemeContext };
export type { CardSkin, ThemeContextValue };
