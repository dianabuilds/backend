import { type ReactNode, useState } from "react";

export default function CollapsibleSection({
  title,
  defaultOpen = true,
  children,
}: {
  title: ReactNode;
  defaultOpen?: boolean;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="rounded border">
      <button
        type="button"
        className="w-full px-3 py-2 flex items-center justify-between text-left"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="font-semibold">{title}</span>
        <span className="text-sm text-gray-500">{open ? "Hide" : "Show"}</span>
      </button>
      {open && <div className="px-3 pb-3">{children}</div>}
    </div>
  );
}
