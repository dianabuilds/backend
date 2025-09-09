import { type ReactNode, useState } from 'react';

export interface TabPlugin {
  name: string;
  render: () => ReactNode;
}

interface Props {
  plugins: TabPlugin[];
}

export default function TabRouter({ plugins }: Props) {
  const [active, setActive] = useState(plugins[0]?.name);

  const current = plugins.find((p) => p.name === active);

  return (
    <div className="flex flex-col flex-1">
      <div className="border-b px-4 flex gap-4">
        {plugins.map((p) => (
          <button
            key={p.name}
            className={`py-2 text-sm ${
              active === p.name ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-600'
            }`}
            onClick={() => setActive(p.name)}
          >
            {p.name}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-auto p-4">{current?.render()}</div>
    </div>
  );
}
