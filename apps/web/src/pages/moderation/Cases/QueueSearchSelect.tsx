import React from 'react';
import { Input, Spinner } from "@ui";
import { apiGet } from '../../../shared/api/client';

export type QueueOption = {
  id: string;
  label: string;
};

type Props = {
  value?: string;
  onChange: (value: string | null) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  onClose?: () => void;
};

const DEBOUNCE_MS = 250;

async function fetchQueues(query: string): Promise<string[]> {
  try {
    const res = await apiGet<{ items?: Array<{ queue?: string | null }> }>(`/api/moderation/cases?size=20&q=${encodeURIComponent(query)}`);
    const items = Array.isArray(res?.items) ? res!.items! : [];
    const values = items
      .map((item) => String(item?.queue ?? '').trim())
      .filter((value) => value.length > 0);
    return Array.from(new Set(values));
  } catch {
    return [];
  }
}

export function QueueSearchSelect({ value, onChange, placeholder = 'Search queue', disabled, autoFocus, onClose }: Props) {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const [inputValue, setInputValue] = React.useState(value ?? '');
  const [query, setQuery] = React.useState('');
  const [options, setOptions] = React.useState<string[]>([]);
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setInputValue(value ?? '');
  }, [value]);

  React.useEffect(() => {
    if (!open) return;
    if (!query.trim()) {
      setOptions([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    const handler = setTimeout(() => {
      (async () => {
        const fetched = await fetchQueues(query);
        if (cancelled) return;
        setOptions(fetched);
        setLoading(false);
      })().catch(() => {
        if (!cancelled) {
          setOptions([]);
          setLoading(false);
        }
      });
    }, DEBOUNCE_MS);
    return () => {
      cancelled = true;
      clearTimeout(handler);
    };
  }, [query, open]);

  const closeDropdown = React.useCallback(() => {
    setOpen(false);
    setQuery('');
    setOptions([]);
    onClose?.();
  }, [onClose]);

  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        closeDropdown();
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [closeDropdown]);

  React.useEffect(() => {
    if (open && autoFocus && inputRef.current) {
      inputRef.current.focus({ preventScroll: true });
    }
  }, [open, autoFocus]);

  const handleSelect = React.useCallback(
    (nextValue: string) => {
      onChange(nextValue);
      setInputValue(nextValue);
      closeDropdown();
    },
    [onChange, closeDropdown],
  );

  const handleClear = React.useCallback(() => {
    onChange(null);
    setInputValue('');
    setQuery('');
    setOptions([]);
    if (!open) onClose?.();
  }, [onChange, open, onClose]);

  return (
    <div ref={containerRef} className="relative">
      <Input
        ref={inputRef}
        label="Queue"
        value={open ? query : inputValue}
        placeholder={placeholder}
        onFocus={() => {
          if (disabled) return;
          setOpen(true);
          setQuery('');
        }}
        onChange={(event) => {
          if (disabled) return;
          setQuery(event.target.value);
          setOpen(true);
        }}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault();
            const target = (open ? query : inputValue).trim();
            if (target) {
              handleSelect(target);
            } else {
              closeDropdown();
            }
          } else if (event.key === 'Escape') {
            event.preventDefault();
            closeDropdown();
          }
        }}
        disabled={disabled}
      />
      {open && (
        <div className="absolute z-30 mt-1 w-full overflow-hidden rounded-md border border-gray-200 bg-white text-sm shadow-lg dark:border-dark-500 dark:bg-dark-700">
          {loading ? (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-gray-500">
              <Spinner size="sm" /> Searching...
            </div>
          ) : query.trim() === '' ? (
            <div className="space-y-1 p-3 text-xs text-gray-500">
              <div>Start typing queue id or name.</div>
              {value && (
                <button type="button" className="text-primary-600 hover:underline" onClick={handleClear}>
                  Clear queue
                </button>
              )}
            </div>
          ) : options.length === 0 ? (
            <div className="space-y-2 px-3 py-2 text-xs text-gray-500">
              <div>No matches</div>
              <button
                type="button"
                className="text-primary-600 hover:underline"
                onClick={() => handleSelect(query.trim())}
              >
                Use "{query.trim()}"
              </button>
            </div>
          ) : (
            options.map((option) => (
              <button
                key={option}
                type="button"
                className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-dark-600"
                onClick={() => handleSelect(option)}
              >
                <span>{option}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default QueueSearchSelect;
