import React, { useMemo } from 'react';

import { ThemeCtx } from './themeContext';
import type { CardSkin } from './themeContext';

type ThemeProviderProps = {
  children: React.ReactNode;
  cardSkin?: CardSkin;
};

export const ThemeProvider = ({ children, cardSkin = 'bordered' }: ThemeProviderProps) => {
  const value = useMemo(() => ({ cardSkin }), [cardSkin]);
  return <ThemeCtx.Provider value={value}>{children}</ThemeCtx.Provider>;
};
