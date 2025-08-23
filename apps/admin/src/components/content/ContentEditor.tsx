import { useState, type ReactNode } from "react";
import GeneralTab, { type GeneralTabProps } from "./GeneralTab";
import StatusBadge from "../StatusBadge";
import VersionBadge from "../VersionBadge";

export const EDITOR_TABS = [
  "General",
  "Content",
  "Relations",
  "AI",
  "Validation",
  "History",
  "Publishing",
  "Notifications",
];

interface ContentEditorProps {
  title: string;
  status?: string;
  version?: number;
  general: GeneralTabProps;
  renderContent: () => ReactNode;
  actions?: ReactNode;
}

export default function ContentEditor({
  title,
  status,
  version,
  general,
  renderContent,
  actions,
}: ContentEditorProps) {
  const [active, setActive] = useState<string>(EDITOR_TABS[0]);

  const renderTab = (tab: string) => {
    switch (tab) {
      case "General":
        return <GeneralTab {...general} />;
      case "Content":
        return renderContent();
      default:
        return <div className="text-sm text-gray-500">No content for {tab} yet.</div>;
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">{title}</h1>
          {status ? <StatusBadge status={status} /> : null}
          {version ? <VersionBadge version={version} /> : null}
        </div>
        {actions}
      </div>
      <div className="flex flex-col flex-1">
        <div className="border-b px-4 flex gap-4">
          {EDITOR_TABS.map((t) => (
            <button
              key={t}
              className={`py-2 text-sm ${
                active === t ? "border-b-2 border-blue-500 text-blue-600" : "text-gray-600"
              }`}
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
