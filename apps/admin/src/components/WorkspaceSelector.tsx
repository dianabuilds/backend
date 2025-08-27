import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { Workspace } from "../api/types";
import { useWorkspace } from "../workspace/WorkspaceContext";

export default function WorkspaceSelector() {
  const { workspaceId, setWorkspace } = useWorkspace();

  const { data, error } = useQuery({
    queryKey: ["workspaces"],
    queryFn: async () => {
      const res = await api.get<Workspace[] | { workspaces: Workspace[] }>(
        "/admin/workspaces",
      );
      const data = res.data;
      if (Array.isArray(data)) return data;
      return data?.workspaces ?? [];
    },
  });

  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);

  useEffect(() => {
    if (!workspaceId && data && data.length > 0) {
      setOpen(true);
    }
  }, [workspaceId, data]);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
      }
    };
    const onMissing = () => setOpen(true);
    document.addEventListener("keydown", onKeyDown);
    window.addEventListener("workspace-missing", onMissing);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      window.removeEventListener("workspace-missing", onMissing);
    };
  }, []);

  const selected = data?.find((ws) => ws.id === workspaceId);

  const items = (data || []).filter(
    (ws) =>
      ws.name.toLowerCase().includes(query.toLowerCase()) ||
      ws.slug.toLowerCase().includes(query.toLowerCase()),
  );

  const onSelect = (ws: Workspace) => {
    setWorkspace(ws);
    setOpen(false);
    setQuery("");
    setActive(0);
  };

  const onInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((a) => (a + 1) % items.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((a) => (a - 1 + items.length) % items.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      const ws = items[active];
      if (ws) onSelect(ws);
    }
  };

  if (error) {
    return (
      <Link to="/login" className="text-blue-600 hover:underline">
        Авторизоваться
      </Link>
    );
  }

  if (data && data.length === 0) {
    return (
      <Link to="/admin/workspaces" className="text-blue-600 hover:underline">
        Создать воркспейс
      </Link>
    );
  }

  return (
    <div className="flex items-center gap-2 mr-4">
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="px-2 py-1 border rounded bg-white text-sm dark:bg-gray-800"
        title={selected ? selected.name : "Выбрать воркспейс"}
      >
        {selected ? selected.name : "Select workspace"}
      </button>
      <Link
        to="/workspaces"
        title="Список воркспейсов"
        className="text-gray-600 hover:text-gray-900"
      >
        📂
      </Link>
      {workspaceId && selected && (
        <Link
          to={`/workspaces/${workspaceId}`}
          title={`Settings for ${selected.name}`}
          className="text-gray-600 hover:text-gray-900"
        >
          ⚙
        </Link>
      )}
      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24">
          <div className="w-80 rounded-lg bg-white dark:bg-gray-800 p-2">
            <input
              autoFocus
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setActive(0);
              }}
              onKeyDown={onInputKeyDown}
              placeholder="Search workspace..."
              className="w-full mb-2 px-2 py-1 border rounded bg-gray-50 dark:bg-gray-700"
            />
            <div className="max-h-60 overflow-y-auto">
              {items.map((ws, idx) => (
                <button
                  key={ws.id}
                  onClick={() => onSelect(ws)}
                  className={`block w-full px-2 py-1 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    idx === active ? "bg-gray-100 dark:bg-gray-700" : ""
                  }`}
                >
                  <div className="font-medium">{ws.name}</div>
                  <div className="text-xs text-gray-500">
                    {ws.slug} • {ws.role}
                  </div>
                </button>
              ))}
              {items.length === 0 && (
                <div className="px-2 py-1 text-sm text-gray-500">No workspaces</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

