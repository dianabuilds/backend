import React from 'react';

import { apiGet } from '../../../../shared/api/client';
import type { UserOption } from '../types';

type UseAuthorSearchResult = {
  authorId: string;
  authorQuery: string;
  options: UserOption[];
  showOptions: boolean;
  handleChange: (value: string) => void;
  handleFocus: () => void;
  handleSelect: (option: UserOption) => void;
  handleClear: () => void;
};

export function useAuthorSearch(): UseAuthorSearchResult {
  const [authorId, setAuthorId] = React.useState('');
  const [authorQuery, setAuthorQuery] = React.useState('');
  const [options, setOptions] = React.useState<UserOption[]>([]);
  const [showOptions, setShowOptions] = React.useState(false);
  const timeoutRef = React.useRef<number | undefined>(undefined);
  const seqRef = React.useRef(0);
  const lastQueryRef = React.useRef('');

  const fetchOptions = React.useCallback(async (value: string, force = false) => {
    const query = value.trim();
    if (!query) {
      setOptions([]);
      lastQueryRef.current = '';
      return;
    }
    if (!force && lastQueryRef.current === query) {
      return;
    }
    lastQueryRef.current = query;
    const seq = ++seqRef.current;
    try {
      const result = await apiGet(`/v1/users/search?q=${encodeURIComponent(query)}&limit=10`);
      if (seqRef.current !== seq) return;
      setOptions(Array.isArray(result) ? (result as UserOption[]) : []);
    } catch (err) {
      if (seqRef.current === seq) {
        console.error('User search failed', err);
        setOptions([]);
      }
    }
  }, []);

  const clearTimeoutIfNeeded = React.useCallback(() => {
    if (timeoutRef.current !== undefined) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = undefined;
    }
  }, []);

  const handleChange = React.useCallback(
    (value: string) => {
      setAuthorQuery(value);
      setShowOptions(true);
      clearTimeoutIfNeeded();
      timeoutRef.current = window.setTimeout(() => {
        void fetchOptions(value);
      }, 250);
    },
    [clearTimeoutIfNeeded, fetchOptions],
  );

  const handleFocus = React.useCallback(() => {
    setShowOptions(true);
    if (authorQuery.trim()) {
      void fetchOptions(authorQuery, true);
    } else {
      lastQueryRef.current = '';
      setOptions([]);
    }
  }, [authorQuery, fetchOptions]);

  const handleSelect = React.useCallback((option: UserOption) => {
    setAuthorId(option.id);
    setAuthorQuery(option.username || option.id);
    setShowOptions(false);
  }, []);

  const handleClear = React.useCallback(() => {
    setAuthorId('');
    setAuthorQuery('');
    setOptions([]);
    setShowOptions(false);
    lastQueryRef.current = '';
  }, []);

  React.useEffect(() => clearTimeoutIfNeeded, [clearTimeoutIfNeeded]);

  return {
    authorId,
    authorQuery,
    options,
    showOptions,
    handleChange,
    handleFocus,
    handleSelect,
    handleClear,
  };
}
