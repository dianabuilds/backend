import { type ReactNode, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import StatusBadge from "../StatusBadge";
import VersionBadge from "../VersionBadge";
import { EDITOR_TABS } from "./ContentEditor.helpers";
import GeneralTab from "./GeneralTab";
import type { GeneralTabProps } from "./GeneralTab.helpers";

interface ContentEditorProps {
  /** Identifier of the node being edited */
  nodeId?: string;
  /** Type of the node (quest, world, etc) */
  node_type?: string;
  /** Editor title */
  title: string;
  /** Current status */
  status?: string;
  /** Available statuses */
  statuses?: string[];
  /** Current version */
  version?: number;
  /** Available versions */
  versions?: number[];
  /** Data for the "General" tab */
  general: GeneralTabProps;
  /** Renderer for the main content tab */
  renderContent: () => ReactNode;
  /** Toolbar displayed on the right side of the header */
  toolbar?: ReactNode;
}

export default function ContentEditor({
  nodeId,
  node_type,
  title,
  status,
  statuses,
  version,
  versions,
  general,
  renderContent,
  toolbar,
}: ContentEditorProps) {
  const [params, setParams] = useSearchParams();
  const initialTab = params.get("tab") || EDITOR_TABS[0];
  const [active, setActive] = useState<string>(initialTab);

  useEffect(() => {
    const tab = params.get("tab");
    if (tab && EDITOR_TABS.includes(tab) && tab !== active) setActive(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params]);

  useEffect(() => {
    setParams((p) => {
      const next = new URLSearchParams(p);
      next.set("tab", active);
      return next;
    });
  }, [active, setParams]);

  const renderTab = (tab: string) => {
    switch (tab) {
      case "General":
        return <GeneralTab {...general} />;
      case "Content":
        return renderContent();
      default:
        return (
          <div className="text-sm text-gray-500">No content for {tab} yet.</div>
        );
    }
  };

  return (
    <div
      data-node-id={nodeId}
      data-node-type={node_type}
      className="flex flex-col h-full"
    >
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold">{title}</h1>
          {statuses?.map((s) => (
            <StatusBadge key={s} status={s} />
          ))}
          {!statuses && status ? <StatusBadge status={status} /> : null}
          {versions?.map((v) => (
            <VersionBadge key={v} version={v} />
          ))}
          {!versions && version ? <VersionBadge version={version} /> : null}
        </div>
        {toolbar}
      </div>
      <div className="flex flex-col flex-1">
        <div className="border-b px-4 flex gap-4">
          {EDITOR_TABS.map((t) => (
            <button
              key={t}
              className={`py-2 text-sm ${
                active === t
                  ? "border-b-2 border-blue-500 text-blue-600"
                  : "text-gray-600"
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
