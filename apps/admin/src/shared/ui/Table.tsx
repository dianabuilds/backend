import type { TableHTMLAttributes } from "react";

export function Table({ className = "", ...props }: TableHTMLAttributes<HTMLTableElement>) {
  return (
    <table
      {...props}
      className={`min-w-full text-sm text-left ${className}`.trim()}
    />
  );
}

export default Table;
