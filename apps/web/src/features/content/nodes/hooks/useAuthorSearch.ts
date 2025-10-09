import React from "react";

import { searchNodeAuthors } from "@shared/api";
import type { NodeUserOption } from "@shared/types/nodes";

type UseAuthorSearchResult = {
  authorId: string;
  authorQuery: string;
  options: NodeUserOption[];
  showOptions: boolean;
  handleChange: (value: string) => void;
  handleFocus: () => void;
  handleSelect: (option: NodeUserOption) => void;
  handleClear: () => void;
};

export function useAuthorSearch(): UseAuthorSearchResult {
  const [authorId, setAuthorId] = React.useState('');
  const [authorQuery, setAuthorQuery] = React.useState('');
  const [options, setOptions] = React.useState<NodeUserOption[]>([]);
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
      const result = await searchNodeAuthors(query, { limit: 10 });
      if (seqRef.current !== seq) return;
      setOptions(result);
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

  const handleSelect = React.useCallback((option: NodeUserOption) => {
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

