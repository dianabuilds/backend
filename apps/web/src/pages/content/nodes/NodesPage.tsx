import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ContentLayout } from '../ContentLayout';
import { Card, Select, Spinner, Skeleton, Pagination, Table } from '@ui';
import { apiGet, apiDelete } from '../../../shared/api/client';
import type { ColumnDef, SortingState } from '@tanstack/react-table';
import { getCoreRowModel, getSortedRowModel, useReactTable, flexRender } from '@tanstack/react-table';
import { EllipsisVerticalIcon, EyeIcon, PencilIcon, TrashIcon, MagnifyingGlassIcon, PlusIcon } from '@heroicons/react/24/outline';

type EmbeddingStatus = 'ready' | 'pending' | 'disabled' | 'error' | 'unknown';

const ALLOWED_EMBEDDING_STATUSES: ReadonlyArray<EmbeddingStatus> = ['ready', 'pending', 'disabled', 'error', 'unknown'];

function isEmbeddingStatus(value: string | null | undefined): value is EmbeddingStatus {
  if (!value) {
    return false;
  }
  return ALLOWED_EMBEDDING_STATUSES.includes(value as EmbeddingStatus);
}

type NodeItem = {
  id: string;
  title?: string | null;
  slug?: string | null;
  author_name?: string | null;
  author_id?: string | null;
  is_public?: boolean;
  status?: string | null;
  updated_at?: string | null;
  embedding_status?: EmbeddingStatus | null;
  embedding_ready?: boolean;
};

const mock: NodeItem[] = Array.from({ length: 12 }).map((_, i) => ({
  id: String(i + 1),
  title: `Demo node ${i + 1}`,
  slug: `node-${i + 1}`,
  status: i % 2 === 0 ? 'published' : 'draft',
  updated_at: new Date(Date.now() - i * 12 * 3600_000).toISOString(),
  author_name: 'demo-user',
  embedding_status: 'ready',
  embedding_ready: true,
}));

function normalizeItem(raw: any): NodeItem {
  const id = raw?.id != null ? String(raw.id) : '';
  const slug = raw?.slug ? String(raw.slug) : id ? `node-${id}` : null;
  const statusRaw = typeof raw?.embedding_status === 'string' ? String(raw.embedding_status).trim().toLowerCase() : null;
  let embeddingStatus: EmbeddingStatus | null = null;
  if (isEmbeddingStatus(statusRaw)) {
    embeddingStatus = statusRaw as EmbeddingStatus;
  }
  let embeddingReady = raw?.embedding_ready === true || (Array.isArray(raw?.embedding) && raw.embedding.length > 0);
  if (embeddingStatus === 'ready') {
    embeddingReady = true;
  } else if (embeddingStatus === 'disabled') {
    embeddingReady = false;
  } else if (!embeddingStatus && embeddingReady) {
    embeddingStatus = 'ready';
  }
  return {
    id,
    title: raw?.title ?? '',
    slug,
    author_name: raw?.author_name ?? raw?.author ?? raw?.author_id ?? null,
    author_id: raw?.author_id ?? null,
    is_public: typeof raw?.is_public === 'boolean' ? raw.is_public : undefined,
    status: raw?.status ?? null,
    updated_at: raw?.updated_at ?? raw?.updatedAt ?? null,
    embedding_status: embeddingStatus,
    embedding_ready: embeddingReady,
  };
}
export default function NodesPage() {
  const navigate = useNavigate();
  const [items, setItems] = React.useState<NodeItem[]>([]);
  const [q, setQ] = React.useState('');
  const [status, setStatus] = React.useState<'all' | 'draft' | 'published'>('all');
  const [page, setPage] = React.useState(1);
  const [pageSize, setPageSize] = React.useState(20);
  const [hasNext, setHasNext] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [openMenuRow, setOpenMenuRow] = React.useState<string | null>(null);
  const [selected, setSelected] = React.useState<Set<string>>(new Set());

  const closeMenu = React.useCallback(() => setOpenMenuRow(null), []);

  React.useEffect(() => {
    const handler = () => setOpenMenuRow(null);
    window.addEventListener('click', handler);
    return () => window.removeEventListener('click', handler);
  }, []);

  async function load() {
    setLoading(true);
    try {
      const offset = (page - 1) * pageSize;
      const url = `/v1/admin/nodes/list?q=${encodeURIComponent(q)}&limit=${pageSize}&offset=${offset}&status=${status}`;
      try {
        const data = await apiGet(url);
        if (Array.isArray(data)) {
          const normalized = data.map(normalizeItem);
          setItems(normalized);
          setHasNext(normalized.length === pageSize);
        } else {
          setItems([]);
          setHasNext(false);
        }
      } catch {
        const filtered = mock.filter((n) =>
          (n.title || '').toLowerCase().includes(q.toLowerCase()) && (status === 'all' || (n.status || 'draft') === status),
        );
        const slice = filtered.slice(offset, offset + pageSize).map(normalizeItem);
        setItems(slice);
        setHasNext(offset + pageSize < filtered.length);
      }
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    const t = setTimeout(load, 200);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [q, status, page, pageSize]);

  React.useEffect(() => {
    setSelected(new Set());
    setOpenMenuRow(null);
  }, [page, items]);

  const renderEmbeddingBadge = React.useCallback((status?: EmbeddingStatus | null) => {
    const normalized = (status ?? 'unknown') as EmbeddingStatus | 'unknown';
    if (normalized === 'ready') return <span className="badge badge-success">Ready</span>;
    if (normalized === 'pending') return <span className="badge badge-warning">Pending</span>;
    if (normalized === 'disabled') return <span className="badge">Disabled</span>;
    if (normalized === 'error') return <span className="badge badge-error">Error</span>;
    return <span className="text-gray-500">—</span>;
  }, []);

  const columns = React.useMemo<ColumnDef<NodeItem>[]>(() => [
    {
      id: 'select',
      header: () => (
        <input
          type="checkbox"
          className="form-checkbox accent-primary-600 align-middle"
          checked={items.length > 0 && items.every((i) => selected.has(i.id))}
          onChange={(e) => {
            const all = new Set(selected);
            if (e.currentTarget.checked) items.forEach((i) => all.add(i.id));
            else items.forEach((i) => all.delete(i.id));
            setSelected(all);
          }}
        />
      ),
      cell: ({ row }) => (
        <input
          type="checkbox"
          className="form-checkbox accent-primary-600 align-middle"
          checked={selected.has(row.original.id)}
          onChange={(e) => {
            const s = new Set(selected);
            if (e.currentTarget.checked) s.add(row.original.id);
            else s.delete(row.original.id);
            setSelected(s);
          }}
        />
      ),
      enableSorting: false,
    },
    {
      id: 'title',
      accessorKey: 'title',
      header: () => 'TITLE',
      cell: ({ row }) => <span className="font-medium text-gray-800 dark:text-dark-100">{row.original.title || '-'}</span>,
      enableSorting: true,
    },
    {
      id: 'slug',
      accessorKey: 'slug',
      header: () => 'SLUG',
      cell: ({ row }) => (
        row.original.slug ? (
          <code className="rounded bg-gray-100 px-2 py-0.5 text-xs text-gray-700 dark:bg-dark-600">{row.original.slug}</code>
        ) : (
          <span className="text-gray-500">-</span>
        )
      ),
      enableSorting: false,
    },
    {
      id: 'author',
      accessorKey: 'author_name',
      header: () => 'AUTHOR',
      cell: ({ row }) => <span className="text-gray-700">{row.original.author_name || '-'}</span>,
      enableSorting: true,
    },
    {
      id: 'status',
      header: () => 'STATUS',
      cell: ({ row }) => {
        const s = (row.original.status || '').toLowerCase();
        const pub = s ? s === 'published' : (row.original.is_public ?? false);
        return <span className={`badge ${pub ? 'badge-success' : 'badge-warning'}`}>{pub ? 'Published' : 'Draft'}</span>;
      },
      enableSorting: true,
    },
    {
      id: 'embedding',
      header: () => 'EMBEDDING',
      cell: ({ row }) => renderEmbeddingBadge(row.original.embedding_status),
      enableSorting: false,
    },
    {
      id: 'updated',
      accessorFn: (r) => r.updated_at || '',
      header: () => 'UPDATED',
      cell: ({ row }) => {
        const val = row.original.updated_at || '';
        const readable = val ? String(val).slice(0, 19).replace('T', ' ') : '-';
        return <span className="text-gray-500">{readable}</span>;
      },
      enableSorting: true,
    },
    {
      id: 'actions',
      header: () => <div className="text-right">ACTIONS</div>,
      cell: ({ row }) => (
        <div
          className="relative flex items-center justify-end"
          role="presentation"
          tabIndex={-1}
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.stopPropagation();
            }
          }}
        >
          <button
            className="inline-flex h-8 w-8 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
            onClick={(e) => {
              e.stopPropagation();
              setOpenMenuRow((v) => (v === row.original.id ? null : row.original.id));
            }}
          >
            <EllipsisVerticalIcon className="h-5 w-5 text-gray-500" />
          </button>
          {openMenuRow === row.original.id && (
            <div className="absolute right-0 top-9 z-30 w-40 rounded-md border border-gray-200 bg-white shadow-lg dark:border-dark-500 dark:bg-dark-700">
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                onClick={() => {
                  closeMenu();
                  navigate(`/nodes/new?id=${encodeURIComponent(row.original.id)}&mode=view`);
                }}
              >
                <EyeIcon className="h-4 w-4" /> View
              </button>
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-dark-600"
                onClick={() => {
                  closeMenu();
                  navigate(`/nodes/new?id=${encodeURIComponent(row.original.id)}`);
                }}
              >
                <PencilIcon className="h-4 w-4" /> Edit
              </button>
              <button
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-500/20"
                onClick={async () => {
                  closeMenu();
                  if (!confirm('Delete this node?')) return;
                  try {
                    await apiDelete(`/v1/admin/nodes/${encodeURIComponent(row.original.id)}`);
                  } catch {}
                  setItems((it) => it.filter((x) => x.id !== row.original.id));
                }}
              >
                <TrashIcon className="h-4 w-4" /> Delete
              </button>
            </div>
          )}
        </div>
      ),
      enableSorting: false,
    },
  ], [items, selected, openMenuRow, closeMenu, navigate, renderEmbeddingBadge]);

  const table = useReactTable({
    data: items,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  function SortIcon({ sorted }: { sorted: false | 'asc' | 'desc' }) {
    return <span className="inline-block w-3 text-gray-500">{sorted === 'asc' ? '^' : sorted === 'desc' ? '¡' : ''}</span>;
  }

  const selectedCount = selected.size;
  const totalRangeStart = (page - 1) * pageSize + (items.length ? 1 : 0);
  const totalRangeEnd = (page - 1) * pageSize + items.length;

  return (
    <ContentLayout context="nodes">
      <Card skin="shadow" className="relative p-4">
        <div className="table-toolbar flex items-center justify-between">
          <h2 className="dark:text-dark-100 truncate text-base font-medium tracking-wide text-gray-800">Nodes</h2>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-2 dark:border-dark-500 dark:bg-dark-700">
              <MagnifyingGlassIcon className="h-4 w-4 text-gray-400" />
              <input
                className="h-8 w-56 bg-transparent text-sm outline-none placeholder:text-gray-400"
                placeholder="Search..."
                value={q}
                onChange={(e) => {
                  setPage(1);
                  setQ(e.target.value);
                }}
              />
            </div>
            {loading && <Spinner size="sm" />}
            <button
              className="inline-flex h-9 w-9 items-center justify-center rounded hover:bg-gray-200/60 dark:hover:bg-dark-500"
              title="Create node"
              onClick={() => navigate('/nodes/new')}
            >
              <PlusIcon className="h-5 w-5 text-gray-600" />
            </button>
          </div>
        </div>

        {selectedCount > 0 && (
          <div className="mt-3 flex flex-wrap items-center gap-3 rounded border border-primary-200 bg-primary-50 p-3 text-sm dark:border-primary-700 dark:bg-primary-900/20">
            <span className="font-medium">Selected: {selectedCount}</span>
            <button
              className="btn-base btn bg-red-600 text-white hover:bg-red-700 disabled:opacity-60"
              onClick={async () => {
                if (!confirm(`Delete ${selectedCount} selected node(s)?`)) return;
                for (const id of Array.from(selected)) {
                  try {
                    await apiDelete(`/v1/admin/nodes/${encodeURIComponent(id)}`);
                  } catch {}
                }
                setItems((it) => it.filter((x) => !selected.has(x.id)));
                setSelected(new Set());
              }}
            >
              Delete selected
            </button>
            <button
              className="btn-base btn bg-gray-150 text-gray-900 hover:bg-gray-200"
              onClick={() => setSelected(new Set())}
            >
              Clear selection
            </button>
          </div>
        )}

        <div className="mt-3 flex items-center gap-3 text-sm text-gray-600 dark:text-dark-200">
          <span>Rows on page: {items.length}</span>
          <Select
            value={String(pageSize)}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(1);
            }}
            className="h-8 w-28 text-xs"
          >
            {[10, 20, 30, 40, 50, 100].map((n) => (
              <option key={n} value={n}>
                {n} rows
              </option>
            ))}
          </Select>
          <Select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value as any);
              setPage(1);
            }}
            className="h-8 w-32 text-xs"
          >
            <option value="all">All</option>
            <option value="published">Published</option>
            <option value="draft">Draft</option>
          </Select>
        </div>

        <div className="mt-4 hide-scrollbar overflow-x-auto overflow-y-visible">
          <Table.Table hover className="min-w-[960px] w-full text-left rtl:text-right">
            <Table.THead>
              {table.getHeaderGroups().map((hg) => (
                <Table.TR key={hg.id}>
                  {hg.headers.map((header, idx) => {
                    const canSort = header.column.getCanSort();
                    const sorted = header.column.getIsSorted();
                    const headerCls =
                      'dark:bg-dark-800 dark:text-dark-100 bg-gray-200 font-semibold text-gray-800 uppercase py-3 px-4 text-left align-middle' +
                      (idx === 0 ? ' first:ltr:rounded-tl-lg first:rtl:rounded-tr-lg' : '') +
                      (idx === hg.headers.length - 1 ? ' last:ltr:rounded-tr-lg last:rtl:rounded-tl-lg' : '');
                    return (
                      <Table.TH key={header.id} className={headerCls} onClick={canSort ? header.column.getToggleSortingHandler() : undefined}>
                        <div className={canSort ? 'flex cursor-pointer items-center gap-2 select-none' : ''}>
                          <span className="flex-1">{header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}</span>
                          {canSort && <SortIcon sorted={sorted || false} />}
                        </div>
                      </Table.TH>
                    );
                  })}
                </Table.TR>
              ))}
            </Table.THead>
            <Table.TBody>
              {loading &&
                Array.from({ length: 6 }).map((_, i) => (
                  <Table.TR key={`sk-${i}`} className="dark:border-b-dark-500 relative border-y border-transparent border-b-gray-200">
                    {columns.map((_, ci) => (
                      <Table.TD key={ci} className="py-2 px-4">
                        <Skeleton className="h-4 w-28" />
                      </Table.TD>
                    ))}
                  </Table.TR>
                ))}
              {!loading &&
                table.getRowModel().rows.map((row) => (
                  <Table.TR key={row.id} className="dark:border-b-dark-500 relative border-y border-transparent border-b-gray-200">
                    {row.getVisibleCells().map((cell) => (
                      <Table.TD key={cell.id} className="py-2 px-4 align-middle">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </Table.TD>
                    ))}
                  </Table.TR>
                ))}
              {!loading && table.getRowModel().rows.length === 0 && (
                <Table.TR>
                  <Table.TD className="py-10 text-center text-sm text-gray-500">No nodes yet</Table.TD>
                </Table.TR>
              )}
            </Table.TBody>
          </Table.Table>
        </div>

        <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between p-4 pt-2">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-gray-500">Rows per page</span>
            <select
              className="form-select h-8 w-20"
              value={String(pageSize)}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setPage(1);
              }}
            >
              {[10, 20, 30, 40, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-1">
            <Pagination page={page} total={hasNext ? page + 1 : page} onChange={setPage} />
          </div>
          <div className="text-sm text-gray-500">
            {totalRangeStart}-{totalRangeEnd} records
          </div>
        </div>
      </Card>
    </ContentLayout>
  );
}
