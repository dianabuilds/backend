import type { ReactNode } from "react";

export default function PageLayout({ title, subtitle, actions, children }: { title: string; subtitle?: string; actions?: ReactNode; children: ReactNode; }) {
  return (
    <div>
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">{title}</h1>
          {subtitle && <div className="text-sm text-gray-500 mt-1">{subtitle}</div>}
        </div>
        {actions && <div className="ml-4">{actions}</div>}
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}
