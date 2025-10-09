import React, { createContext, useContext, useMemo } from 'react';
import type { ReactNode, TableHTMLAttributes } from 'react';
import clsx from 'clsx';

import { TablePagination } from './TablePagination';

type TablePreset = 'base' | 'management' | 'surface' | 'analytics';

type TableContextValue = {
  preset: TablePreset;
  headerSticky: boolean;
  actions?: ReactNode;
  zebra: boolean;
  hover: boolean;
};

const defaultTableContext: TableContextValue = {
  preset: 'base',
  headerSticky: false,
  actions: undefined,
  zebra: false,
  hover: false,
};

const TableContext = createContext<TableContextValue>(defaultTableContext);

function useTableContext(): TableContextValue {
  return useContext(TableContext);
}

const ROW_BORDER_CLASSNAMES: Record<TablePreset, string> = {
  base: 'border-b border-gray-100 last:border-b-0 dark:border-gray-800',
  management: 'border-b border-slate-200/70 last:border-b-0 dark:border-slate-800/70',
  surface: 'border-b border-gray-100 last:border-b-0 dark:border-gray-800',
  analytics: 'border-b border-slate-200/60 last:border-b-0 dark:border-slate-700/60',
};

const TH_CLASSNAMES: Record<TablePreset, string> = {
  base: 'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300',
  management: 'px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-200',
  surface: 'px-5 py-4 text-left text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-200',
  analytics: 'px-4 py-3 text-left text-[11px] font-semibold uppercase tracking-[0.28em] text-slate-500 dark:text-slate-300',
};

const TD_CLASSNAMES: Record<TablePreset, string> = {
  base: 'px-4 py-3 text-sm text-gray-700 dark:text-gray-100',
  management: 'px-4 py-3 text-sm text-slate-700 dark:text-slate-200',
  surface: 'px-5 py-4 text-sm text-gray-700 dark:text-gray-100',
  analytics: 'px-4 py-3 text-sm text-slate-700 dark:text-slate-100',
};

const ACTIONS_TEXT_CLASS: Record<TablePreset, string> = {
  base: 'text-gray-600 dark:text-gray-200',
  management: 'text-slate-600 dark:text-slate-200',
  surface: 'text-gray-600 dark:text-gray-200',
  analytics: 'text-slate-500 dark:text-slate-300',
};

const STATE_TITLE_CLASS: Record<TablePreset, string> = {
  base: 'text-gray-700 dark:text-gray-100',
  management: 'text-slate-700 dark:text-slate-100',
  surface: 'text-gray-700 dark:text-gray-100',
  analytics: 'text-slate-200 dark:text-slate-50',
};

const STATE_TEXT_CLASS: Record<TablePreset, string> = {
  base: 'text-gray-500 dark:text-gray-300',
  management: 'text-slate-600 dark:text-slate-300',
  surface: 'text-gray-500 dark:text-gray-300',
  analytics: 'text-slate-400 dark:text-slate-300',
};

const LOADING_BAR_CLASS: Record<TablePreset, string> = {
  base: 'bg-gray-200 dark:bg-gray-700',
  management: 'bg-slate-200 dark:bg-slate-700',
  surface: 'bg-gray-200 dark:bg-gray-700',
  analytics: 'bg-slate-200/80 dark:bg-slate-700/70',
};
const PRESET_TABLE_CLASSNAMES: Record<TablePreset, string> = {
  base: 'table--base text-sm text-gray-900 dark:text-gray-100',
  management: 'table--management text-sm text-gray-800 dark:text-gray-50 align-middle',
  surface: 'table--surface text-sm text-gray-900 dark:text-gray-50 bg-white dark:bg-gray-900 shadow-sm rounded-xl overflow-hidden',
  analytics: 'table--analytics text-sm text-slate-800 dark:text-slate-100 align-middle',
};

const HEADER_BACKGROUNDS: Record<TablePreset, string> = {
  base: 'bg-gray-50 dark:bg-gray-800',
  management: 'bg-slate-50 dark:bg-slate-900',
  surface: 'bg-white dark:bg-gray-900',
  analytics: 'bg-transparent text-slate-500 dark:text-slate-300 backdrop-blur-sm',
};

export type TableProps = TableHTMLAttributes<HTMLTableElement> & {
  zebra?: boolean;
  hover?: boolean;
  preset?: TablePreset;
  actions?: ReactNode;
  headerSticky?: boolean;
};

const TableComponent = React.forwardRef<HTMLTableElement, TableProps>(function TableComponent(
  { className = '', zebra = false, hover = false, preset = 'base', actions, headerSticky = false, children, ...rest },
  ref
) {
  const value = useMemo(
    () => ({ preset, headerSticky, actions, zebra, hover }),
    [preset, headerSticky, actions, zebra, hover]
  );

  const tableClass = clsx(
    'table w-full border-collapse',
    PRESET_TABLE_CLASSNAMES[preset],
    zebra && 'table--zebra',
    hover && 'table--hover',
    className
  );

  return (
    <TableContext.Provider value={value}>
      <table ref={ref} className={tableClass} {...rest}>
        {children}
      </table>
    </TableContext.Provider>
  );
});

export type TableActionsProps = React.HTMLAttributes<HTMLTableCaptionElement> & {
  children?: ReactNode;
};

function TableActions({ className = '', children, ...rest }: TableActionsProps) {
  const { actions, preset } = useTableContext();
  const content = children ?? actions;
  if (!content) return null;
  return (
    <caption
      className={clsx(
        'table-actions caption-top mb-3 flex w-full items-center justify-between gap-3 text-sm',
        ACTIONS_TEXT_CLASS[preset],
        className
      )}
      {...rest}
    >
      {content}
    </caption>
  );
}

export type TableStateProps = {
  colSpan?: number;
  title?: string;
  description?: string;
  icon?: ReactNode;
  action?: ReactNode;
  className?: string;
};

function TableEmpty({
  colSpan = 1,
  title = 'No data yet',
  description = 'Once records appear, you will see them here.',
  icon,
  action,
  className = '',
}: TableStateProps) {
  const { preset } = useTableContext();
  return (
    <tr className="table-empty">
      <td
        colSpan={colSpan}
        className={clsx(
          'px-6 py-12 text-center text-sm',
          STATE_TEXT_CLASS[preset],
          className
        )}
      >
        <div className="mx-auto flex max-w-md flex-col items-center gap-3">
          {icon}
          <div className={clsx('text-base font-medium', STATE_TITLE_CLASS[preset])}>{title}</div>
          {description ? (
            <div className={clsx('text-sm', STATE_TEXT_CLASS[preset])}>{description}</div>
          ) : null}
          {action}
        </div>
      </td>
    </tr>
  );
}

export type TableErrorProps = TableStateProps & {
  onRetry?: () => void;
  retryLabel?: string;
};

function TableError({
  colSpan = 1,
  title = 'Could not load data',
  description = 'Something went wrong while fetching this dataset.',
  icon,
  action,
  onRetry,
  retryLabel = 'Try again',
  className = '',
}: TableErrorProps) {
  return (
    <tr className="table-error">
      <td
        colSpan={colSpan}
        className={clsx(
          'px-6 py-12 text-center text-sm text-red-600 dark:text-red-300',
          className
        )}
      >
        <div className="mx-auto flex max-w-md flex-col items-center gap-3">
          {icon}
          <div className="text-base font-medium text-red-600 dark:text-red-300">{title}</div>
          {description ? <div className="text-sm text-red-500 dark:text-red-200">{description}</div> : null}
          {action ??
            (onRetry ? (
              <button
                type="button"
                className="inline-flex items-center justify-center gap-2 rounded-md border border-red-200 bg-white px-3 py-1.5 text-sm font-medium text-red-600 shadow-sm hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:border-red-500/40 dark:bg-transparent dark:hover:bg-red-500/10"
                onClick={onRetry}
              >
                {retryLabel}
              </button>
            ) : null)}
        </div>
      </td>
    </tr>
  );
}

export type TableLoadingProps = {
  colSpan?: number;
  rows?: number;
  linesPerRow?: number;
  className?: string;
};

function TableLoading({ colSpan = 1, rows = 3, linesPerRow = 2, className = '' }: TableLoadingProps) {
  const { preset } = useTableContext();
  return (
    <>
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <tr key={rowIndex} className="table-loading">
          <td colSpan={colSpan} className={clsx('px-6 py-4', className)}>
            <div className="flex flex-col gap-2">
              {Array.from({ length: linesPerRow }).map((__, lineIndex) => (
                <div
                  key={lineIndex}
                  className={clsx('h-3 w-full animate-pulse rounded', LOADING_BAR_CLASS[preset])}
                />
              ))}
            </div>
          </td>
        </tr>
      ))}
    </>
  );
}

export function THead({ className = '', children, ...rest }: React.HTMLAttributes<HTMLTableSectionElement>) {
  const { headerSticky, preset } = useTableContext();
  return (
    <thead
      className={clsx(
        'table-thead text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-300',
        headerSticky && `sticky top-0 z-20 shadow-sm ${HEADER_BACKGROUNDS[preset]}`,
        !headerSticky && HEADER_BACKGROUNDS[preset],
        className
      )}
      {...rest}
    >
      {children}
    </thead>
  );
}

export function TBody({ className = '', children, ...rest }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return (
    <tbody
      className={clsx('table-tbody divide-y divide-gray-100 dark:divide-gray-800', className)}
      {...rest}
    >
      {children}
    </tbody>
  );
}

export function TR({ className = '', children, ...rest }: React.HTMLAttributes<HTMLTableRowElement>) {
  const { zebra, hover, preset } = useTableContext();
  return (
    <tr
      className={clsx(
        'table-tr',
        ROW_BORDER_CLASSNAMES[preset],
        zebra && 'even:bg-gray-50 dark:even:bg-gray-900',
        hover && 'transition-colors hover:bg-gray-50 dark:hover:bg-gray-900',
        className
      )}
      {...rest}
    >
      {children}
    </tr>
  );
}

export function TH({ className = '', children, ...rest }: React.ThHTMLAttributes<HTMLTableCellElement>) {
  const { preset } = useTableContext();
  return (
    <th
      className={clsx('table-th', TH_CLASSNAMES[preset], className)}
      {...rest}
    >
      {children}
    </th>
  );
}

export function TD({ className = '', children, ...rest }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  const { preset } = useTableContext();
  return (
    <td className={clsx('table-td', TD_CLASSNAMES[preset], className)} {...rest}>
      {children}
    </td>
  );
}

type TableCompound = React.ForwardRefExoticComponent<TableProps & React.RefAttributes<HTMLTableElement>> & {
  Actions: typeof TableActions;
  Empty: typeof TableEmpty;
  Error: typeof TableError;
  Loading: typeof TableLoading;
  THead: typeof THead;
  TBody: typeof TBody;
  TR: typeof TR;
  TH: typeof TH;
  TD: typeof TD;
  Pagination: typeof TablePagination;
};

const Table = Object.assign(TableComponent, {
  Actions: TableActions,
  Empty: TableEmpty,
  Error: TableError,
  Loading: TableLoading,
  THead,
  TBody,
  TR,
  TH,
  TD,
  Pagination: TablePagination,
}) as TableCompound;

export { Table, TableActions, TableEmpty, TableError, TableLoading, TablePagination };


















