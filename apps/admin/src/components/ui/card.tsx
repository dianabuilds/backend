import type { HTMLAttributes } from "react";

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded border bg-white shadow-sm dark:border-gray-700 dark:bg-gray-800 ${className ?? ""}`}
      {...props}
    />
  );
}

export function CardContent({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={`p-4 ${className ?? ""}`} {...props} />;
}

