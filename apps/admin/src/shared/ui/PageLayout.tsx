import type { ReactNode } from "react";

interface PageLayoutProps {
  title: string;
  children: ReactNode;
  actions?: ReactNode;
}

export function PageLayout({ title, actions, children }: PageLayoutProps) {
  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <h1 className="text-2xl font-bold mr-auto">{title}</h1>
        {actions}
      </div>
      {children}
    </div>
  );
}

export default PageLayout;
