import React from 'react';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';

export function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-neutral-100 text-gray-900 dark:bg-dark-900 dark:text-white flex">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto px-6 pb-12 pt-6 lg:px-12">
          <div className="mx-auto w-full max-w-[1600px] lg:max-w-[1800px] space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}

