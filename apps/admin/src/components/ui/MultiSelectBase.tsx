import React from "react";

export type MultiSelectBaseProps<T> = {
  items: T[];
  values: T[];
  onChange: (values: T[]) => void;
  getKey: (item: T) => string;
  getLabel: (item: T) => string;
  renderItem?: (item: T, selected: boolean) => React.ReactNode;
};

export default function MultiSelectBase<T>({
  items,
  values,
  onChange,
  getKey,
  getLabel,
  renderItem,
}: MultiSelectBaseProps<T>) {
  const selectedKeys = values.map((v) => getKey(v));

  return (
    <select
      multiple
      value={selectedKeys}
      onChange={(e) => {
        const options = Array.from(e.target.selectedOptions).map((o) => o.value);
        const selectedItems = items.filter((i) => options.includes(getKey(i)));
        onChange(selectedItems);
      }}
    >
      {items.map((item) => {
        const key = getKey(item);
        const selected = selectedKeys.includes(key);
        return (
          <option key={key} value={key}>
            {renderItem ? renderItem(item, selected) : getLabel(item)}
          </option>
        );
      })}
    </select>
  );
}
