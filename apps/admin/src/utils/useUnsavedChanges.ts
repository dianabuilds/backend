import { useEffect } from 'react';

/**
 * Registers a beforeunload listener to warn the user about unsaved changes.
 * Pass a boolean flag that indicates whether there are unsaved changes.
 */
export function useUnsavedChanges(unsaved: boolean): void {
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!unsaved) return;
      e.preventDefault();
      // Chrome requires returnValue to be set
      e.returnValue = '';
    };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [unsaved]);
}
