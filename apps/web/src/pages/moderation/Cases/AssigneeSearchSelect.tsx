import React from 'react';
import { Input, Spinner } from "@ui";
import { apiGet } from '@shared/api/client';

export type AssigneeOption = {
  id: string;
  username?: string | null;
  email?: string | null;
};

type Props = {
  value?: string;
  label?: string;
  onChange: (option: { id: string; label: string } | null) => void;
  placeholder?: string;
  disabled?: boolean;
  autoFocus?: boolean;
  onClose?: () => void;
};

const DEBOUNCE_MS = 250;

function optionLabel(option: AssigneeOption): string {
  return option.username || option.email || option.id;
}

export function AssigneeSearchSelect({ value, label, onChange, placeholder = 'Search user', disabled, autoFocus, onClose }: Props) {
  const containerRef = React.useRef<HTMLDivElement | null>(null);
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const [inputValue, setInputValue] = React.useState(label || value || '');
  const [query, setQuery] = React.useState('');
  const [options, setOptions] = React.useState<AssigneeOption[]>([]);
  const [open, setOpen] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setInputValue(label || value || '');
  }, [value, label]);

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
        try {
          const response = await apiGet<{ items?: AssigneeOption[] }>(`/api/moderation/users?limit=8&q=${encodeURIComponent(query)}`);
          if (cancelled) return;
          setOptions(Array.isArray(response?.items) ? response.items : []);
        } catch {
          if (!cancelled) setOptions([]);
        } finally {
          if (!cancelled) setLoading(false);
        }
      })().catch(() => {
        if (!cancelled) {
          setLoading(false);
          setOptions([]);
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
    (option: AssigneeOption) => {
      const display = optionLabel(option);
      onChange({ id: option.id, label: display });
      setInputValue(display);
      closeDropdown();
    },
    [onChange, closeDropdown],
  );

  const handleClear = React.useCallback(() => {
    onChange(null);
    setInputValue('');
    setQuery('');
    setOptions([]);
    if (!open) {
      onClose?.();
    }
  }, [onChange, open, onClose]);

  return (
    <div ref={containerRef} className="relative">
      <Input
        ref={inputRef}
        label="Assignee"
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
        disabled={disabled}
      />
      {open && (
        <div className="absolute z-10 mt-1 w-full overflow-hidden rounded-md border border-gray-200 bg-white text-sm shadow-lg dark:border-dark-500 dark:bg-dark-700">
          {loading ? (
            <div className="flex items-center gap-2 px-3 py-2 text-xs text-gray-500">
              <Spinner size="sm" /> Searching...
            </div>
          ) : query.trim() === '' ? (
            <div className="space-y-1 p-3 text-xs text-gray-500">
              <div>Start typing username or email.</div>
              {value && (
                <button type="button" className="text-primary-600 hover:underline" onClick={handleClear}>
                  Clear assignee
                </button>
              )}
            </div>
          ) : options.length === 0 ? (
            <div className="px-3 py-2 text-xs text-gray-500">No matches</div>
          ) : (
            options.map((option) => (
              <button
                key={option.id}
                type="button"
                className="flex w-full items-center justify-between gap-3 px-3 py-2 text-left hover:bg-gray-100 dark:hover:bg-dark-600"
                onClick={() => handleSelect(option)}
              >
                <span>{optionLabel(option)}</span>
                <span className="text-xs text-gray-400">{option.id}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default AssigneeSearchSelect;
