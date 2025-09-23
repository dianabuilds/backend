import React from 'react';

type TabItem = { key: string; label: React.ReactNode };

type TabsProps = {
  items: TabItem[];
  value: string;
  onChange: (key: string) => void;
  className?: string;
};

export function Tabs({ items, value, onChange, className = '' }: TabsProps) {
  return (
    <div className={`border-b border-gray-200 dark:border-dark-600 ${className}`}> 
      <ul className="-mb-px flex flex-wrap gap-2">
        {items.map((it) => {
          const active = it.key === value;
          return (
            <li key={it.key}>
              <button
                className={`px-3 py-2 text-sm font-medium border-b-2 ${active ? 'border-primary-600 text-primary-700' : 'border-transparent text-gray-600 hover:text-gray-800 hover:border-gray-300'}`}
                onClick={() => onChange(it.key)}
              >
                {it.label}
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default Tabs;

