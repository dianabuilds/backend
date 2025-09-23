import React from 'react';

type TagInputProps = {
  value: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
  label?: string;
  className?: string;
  disabled?: boolean;
};

export function TagInput({ value, onChange, placeholder = 'tag, another', label, className = '', disabled = false }: TagInputProps) {
  const [text, setText] = React.useState('');

  const add = (raw: string) => {
    if (disabled) return;
    const t = raw.trim();
    if (!t) return;
    if (value.includes(t)) return;
    onChange([...value, t]);
  };

  const remove = (t: string) => {
    if (disabled) return;
    onChange(value.filter((x) => x !== t));
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (disabled) return;
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      add(text);
      setText('');
    } else if (e.key === 'Backspace' && !text && value.length > 0) {
      remove(value[value.length - 1]);
    }
  };

  const onBlur = () => {
    if (disabled) return;
    if (text.trim()) {
      add(text);
      setText('');
    }
  };

  return (
    <div className={`input-root ${className}`}>
      {label && (
        <label className="input-label">
          <span className="input-label">{label}</span>
        </label>
      )}
      <div className={`input-wrapper relative ${label ? 'mt-1.5' : ''}`}>
        <div
          className={`min-h-10 flex flex-wrap items-center gap-1 rounded-lg border border-gray-300 px-2 py-1 text-sm ${
            disabled
              ? 'bg-gray-100 text-gray-500 dark:bg-dark-700 dark:text-dark-300'
              : 'focus-within:border-primary-600 dark:border-dark-450 dark:focus-within:border-primary-500'
          }`}
        >
          {value.map((t) => (
            <span key={t} className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-dark-600">
              #{t}
              <button
                type="button"
                className="text-gray-400 hover:text-gray-600 disabled:opacity-40"
                aria-label="remove"
                onClick={() => remove(t)}
                disabled={disabled}
              >
                x
              </button>
            </span>
          ))}
          <input
            className="flex-1 min-w-[8rem] bg-transparent outline-none placeholder:text-gray-400 disabled:cursor-not-allowed disabled:opacity-60"
            placeholder={placeholder}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={onKeyDown}
            onBlur={onBlur}
            disabled={disabled}
          />
        </div>
      </div>
    </div>
  );
}
