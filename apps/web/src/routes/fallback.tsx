import React from 'react';

export function RouteFallback(): React.ReactElement {
  return (
    <div className="flex min-h-[320px] flex-1 items-center justify-center py-16 text-sm text-gray-500 dark:text-dark-200" role="status">
      {"Загрузка…"}
    </div>
  );
}
