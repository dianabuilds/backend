import { type ReactNode, useEffect } from "react";

import StatusBadge from "../StatusBadge";
import VersionBadge from "../VersionBadge";
import TabRouter, { type TabPlugin } from "../TabRouter";
import GeneralTab from "./GeneralTab";
import type { GeneralTabProps } from "./GeneralTab.helpers";
import ContentTab from "./ContentTab";
import ValidationTab from "./ValidationTab";
import PublishingTab from "./PublishingTab";
import RelationsTab from "./relations/RelationsTab";
import type { OutputData } from "../../types/editorjs";

interface ContentTabProps {
  initial?: OutputData;
  onSave?: (data: OutputData) => Promise<void> | void;
  storageKey?: string;
}

interface ContentEditorProps {
  nodeId?: string;
  node_type?: string;
  title: string;
  slug?: string;
  status?: string;
  statuses?: string[];
  version?: number;
  versions?: number[];
  general: GeneralTabProps;
  content: ContentTabProps;
  toolbar?: ReactNode;
  onSave?: () => void;
}

export default function ContentEditor({
  nodeId,
  node_type,
  title,
  slug,
  status,
  statuses,
  version,
  versions,
  general,
  content,
  toolbar,
  onSave,
}: ContentEditorProps) {
  const plugins: TabPlugin[] = [
    { name: "General", render: () => <GeneralTab {...general} /> },
    { name: "Content", render: () => <ContentTab {...content} /> },
    {
      name: "Relations",
      render: () => (
        <RelationsTab nodeId={nodeId} slug={slug} nodeType={node_type} />
      ),
    },
    { name: "Validation", render: () => <ValidationTab /> },
    { name: "Publishing", render: () => <PublishingTab /> },
  ];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === "s" || e.key === "Enter")) {
        e.preventDefault();
        onSave?.();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSave]);

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
      <TabRouter plugins={plugins} />
    </div>
  );
}
