// @ts-nocheck
import React from 'react';

export type Recent429Item = {
  path: string;
  ip: string;
  rule: string;
  ts: string;
};

interface Props {
  items: Recent429Item[];
  className?: string;
  emptyText?: string;
}

export default function Recent429Table({
  items,
  className = '',
  emptyText = 'No recent 429 errors.',
}: Props) {
  if (!items?.length) {
    return <p className="text-sm text-gray-500">{emptyText}</p>;
  }
  return (
    <table className={`min-w-full text-sm ${className}`.trim()}>
      <thead>
        <tr className="border-b">
          <th className="p-2 text-left">Path</th>
          <th className="p-2 text-left">IP</th>
          <th className="p-2 text-left">Rule</th>
          <th className="p-2 text-left">Time</th>
        </tr>
      </thead>
      <tbody>
        {items.map((r, i) => (
          <tr key={i} className="border-b">
            <td className="p-2 font-mono">{r.path}</td>
            <td className="p-2">{r.ip}</td>
            <td className="p-2">{r.rule}</td>
            <td className="p-2">{r.ts}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
