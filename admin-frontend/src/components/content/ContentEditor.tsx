import { useState, type ReactNode } from "react";

interface ContentEditorProps {
  title: string;
  tabs: string[];
  renderTab: (tab: string) => ReactNode;
  actions?: ReactNode;
}

export default function ContentEditor({ title, tabs, renderTab, actions }: ContentEditorProps) {
  const [active, setActive] = useState<string>(tabs[0]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b p-4">
        <h1 className="text-xl font-semibold">{title}</h1>
        {actions}
      </div>
      <div className="flex flex-col flex-1">
        <div className="border-b px-4 flex gap-4">
          {tabs.map((t) => (
            <button
              key={t}
              className={`py-2 text-sm ${active === t ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-600"}`}
              onClick={() => setActive(t)}
            >
              {t}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-auto p-4">{renderTab(active)}</div>
      </div>
    </div>
  );
}
