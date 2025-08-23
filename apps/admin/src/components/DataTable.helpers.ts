import type { ReactNode } from "react";

export type Column<T> = {
  key: string;
  title: string;
  width?: string | number;
  render?: (row: T) => ReactNode;
  accessor?: (row: T) => ReactNode;
  className?: string;
};
