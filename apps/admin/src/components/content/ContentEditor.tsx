import { type ReactNode, useEffect } from "react";

import type { OutputData } from "../../types/editorjs";
import StatusBadge from "../StatusBadge";
import VersionBadge from "../VersionBadge";
import ContentTab from "./ContentTab";
import GeneralTab from "./GeneralTab";
import type { GeneralTabProps } from "./GeneralTab.helpers";

interface ContentTabProps {
  initial?: OutputData;
  onSave?: (data: OutputData) => Promise<void> | void;
  storageKey?: string;
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
  onSave?: () => void;
  onClose?: () => void;
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
  onSave,
  onClose,
}: ContentEditorProps) {

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose?.();
        return;
      }
      if (!(e.ctrlKey || e.metaKey)) return;

      if (e.key === "s") {
        e.preventDefault();
        onSave?.();
        return;
      }

      if (e.key === "Enter") {
        e.preventDefault();
        const btn = Array.from(
          document.querySelectorAll<HTMLButtonElement>("button"),
        ).find((b) => b.textContent?.trim() === "Save & Next");
        btn?.click();
        return;
      }

      if (e.shiftKey && (e.key === "I" || e.key === "i")) {
        e.preventDefault();
        const plus = document.querySelector<HTMLButtonElement>(
          ".ce-toolbar__plus",
        );
        plus?.click();
        window.setTimeout(() => {
          const image = document.querySelector<HTMLElement>(
            '.ce-popover-item[data-tool="image"]',
          );
          image?.click();
        }, 0);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onSave, onClose]);

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
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <GeneralTab {...general} />
        <ContentTab {...content} />
      </div>
    </div>
  );
}
