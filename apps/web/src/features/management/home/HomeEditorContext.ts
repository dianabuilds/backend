import * as React from 'react';
import type { HomeEditorContextValue } from './types';

export const HomeEditorContext = React.createContext<HomeEditorContextValue | undefined>(undefined);

export function useHomeEditorContext(): HomeEditorContextValue {
  const ctx = React.useContext(HomeEditorContext);
  if (!ctx) {
    throw new Error('useHomeEditorContext must be used within HomeEditorProvider');
  }
  return ctx;
}