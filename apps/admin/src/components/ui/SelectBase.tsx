import React from 'react';

export type SelectBaseProps<T> = {
  items: T[];
  value?: T;
  onChange: (value: T | undefined) => void;
  getKey: (item: T) => string;
  getLabel: (item: T) => string;
  renderItem?: (item: T, selected: boolean) => React.ReactNode;
};

export default function SelectBase<T>({
  items,
  value,
  onChange,
  getKey,
  getLabel,
  renderItem,
}: SelectBaseProps<T>) {
  const selectedKey = value ? getKey(value) : '';

  return (
    <select
      value={selectedKey}
      onChange={(e) => {
        const item = items.find((i) => getKey(i) === e.target.value);
        onChange(item);
      }}
    >
      {items.map((item) => {
        const key = getKey(item);
        const selected = key === selectedKey;
        return (
          <option key={key} value={key}>
            {renderItem ? renderItem(item, selected) : getLabel(item)}
          </option>
        );
      })}
    </select>
  );
}
