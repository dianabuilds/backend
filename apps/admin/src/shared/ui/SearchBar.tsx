import type { FormEvent } from 'react';

import { Button } from './Button';
import { TextInput } from './TextInput';

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onSearch: () => void | Promise<void>;
  placeholder?: string;
}

export function SearchBar({ value, onChange, onSearch, placeholder }: SearchBarProps) {
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await onSearch();
  };

  const handleReset = () => {
    onChange('');
    setTimeout(() => {
      void onSearch();
    }, 0);
  };

  return (
    <form onSubmit={handleSubmit} className="flex items-center gap-2">
      <TextInput
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
      <Button type="submit">Search</Button>
      {value !== '' && (
        <Button type="button" onClick={handleReset}>
          Reset
        </Button>
      )}
    </form>
  );
}

export default SearchBar;
