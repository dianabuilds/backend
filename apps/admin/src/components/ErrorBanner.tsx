import React from "react";

type Props = {
  message?: string | null;
  code?: string | null;
  onClose?: () => void;
  className?: string;
  children?: React.ReactNode;
};

export default function ErrorBanner({ message, code, onClose, className, children }: Props) {
  if (!message && !children) return null;
  return (
    <div className={`border border-red-300 bg-red-50 text-red-700 rounded p-2 ${className || ""}`}>
      <div className="flex justify-between items-start gap-3">
        <div className="text-sm">
          {code ? <span className="font-mono mr-2 text-xs px-1.5 py-0.5 rounded bg-red-100 border border-red-200">{code}</span> : null}
          {message}
        </div>
        {onClose ? (
          <button onClick={onClose} className="text-xs text-red-600 hover:underline">закрыть</button>
        ) : null}
      </div>
      {children ? <div className="mt-2">{children}</div> : null}
    </div>
  );
}
