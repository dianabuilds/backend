import { type ReactNode } from "react";

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
}

interface ContentEditorProps {
  nodeId?: string;
  node_type?: string;
  title: string;
  status?: string;
  statuses?: string[];
  version?: number;
  versions?: number[];
  general: GeneralTabProps;
  content: ContentTabProps;
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
  content,
  toolbar,
}: ContentEditorProps) {
  const plugins: TabPlugin[] = [
    { name: "General", render: () => <GeneralTab {...general} /> },
    { name: "Content", render: () => <ContentTab {...content} /> },
    {
      name: "Relations",
      render: () => (
        <RelationsTab nodeId={nodeId} slug={general.slug} nodeType={node_type} />
      ),
    },
    { name: "Validation", render: () => <ValidationTab /> },
    { name: "Publishing", render: () => <PublishingTab /> },
  ];

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
