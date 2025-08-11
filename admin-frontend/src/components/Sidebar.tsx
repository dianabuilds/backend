import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { getAdminMenu, MenuItem } from "../api/menu";
import { useAuth } from "../auth/AuthContext";

export default function Sidebar() {
  const { logout } = useAuth();
  const location = useLocation();
  const [items, setItems] = useState<MenuItem[] | null>(null);
  const [etag, setEtag] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState<Record<string, boolean>>({});

  const load = async () => {
    try {
      const resp = await getAdminMenu(etag ?? undefined);
      if (resp.status !== 304 && resp.items) {
        setItems(resp.items);
        setEtag(resp.etag ?? null);
      }
      setError(null);
    } catch (e: any) {
      if (e.message === "unauthorized") {
        logout();
      } else {
        setError(e.message || "Failed to load menu");
      }
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (items) {
      const state: Record<string, boolean> = {};
      items.forEach((i) => {
        const v = localStorage.getItem(`menu-open-${i.id}`);
        state[i.id] = v === "1";
      });
      setOpen((prev) => ({ ...state, ...prev }));
    }
  }, [items]);

  const activeId = useMemo(() => {
    if (!items) return null;
    let best: { id: string; path: string } | null = null;
    const check = (list: MenuItem[]) => {
      list.forEach((item) => {
        if (item.path && location.pathname.startsWith(item.path)) {
          if (!best || item.path.length > best.path.length) {
            best = { id: item.id, path: item.path };
          }
        }
        check(item.children);
      });
    };
    check(items);
    return best?.id ?? null;
  }, [items, location.pathname]);

  useEffect(() => {
    if (!items || !activeId) return;
    const parents: string[] = [];
    const find = (list: MenuItem[], acc: string[]): boolean => {
      for (const item of list) {
        if (item.id === activeId) {
          parents.push(...acc);
          return true;
        }
        if (item.children.length && find(item.children, [...acc, item.id])) {
          return true;
        }
      }
      return false;
    };
    find(items, []);
    if (parents.length) {
      setOpen((prev) => {
        const updated = { ...prev };
        parents.forEach((p) => (updated[p] = true));
        return updated;
      });
    }
  }, [activeId, items]);

  const toggle = (id: string) => {
    setOpen((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      localStorage.setItem(`menu-open-${id}`, next[id] ? "1" : "0");
      return next;
    });
  };

  const renderItems = (list: MenuItem[]) => (
    <ul>
      {list.map((item) => {
        if (item.children.length > 0 && !item.path) {
          const isOpen = !!open[item.id];
          return (
            <li key={item.id}>
              <button
                onClick={() => toggle(item.id)}
                aria-expanded={isOpen}
                className="flex w-full justify-between p-2"
              >
                <span>{item.label}</span>
              </button>
              {isOpen && renderItems(item.children)}
            </li>
          );
        }
        const isActive = item.id === activeId;
        const content = item.external ? (
          <a
            href={item.path ?? "#"}
            target="_blank"
            rel="noreferrer"
            className={`block p-2 ${isActive ? "bg-gray-200 dark:bg-gray-800" : ""}`}
          >
            {item.label}
          </a>
        ) : (
          <NavLink
            to={item.path ?? "#"}
            aria-current={isActive ? "page" : undefined}
            className={`block p-2 ${isActive ? "bg-gray-200 dark:bg-gray-800" : ""}`}
          >
            {item.label}
          </NavLink>
        );
        return <li key={item.id}>{content}</li>;
      })}
    </ul>
  );

  if (error) {
    return (
      <nav role="navigation" aria-label="Admin menu" className="w-64 p-4">
        <div className="mb-2 text-red-600">{error}</div>
        <ul>
          <li>
            <NavLink to="/">Dashboard</NavLink>
          </li>
        </ul>
        <button onClick={load} className="mt-2 underline">
          Retry
        </button>
      </nav>
    );
  }

  if (!items) {
    return (
      <nav role="navigation" aria-label="Admin menu" className="w-64 p-4">
        Loading...
      </nav>
    );
  }

  return (
    <nav role="navigation" aria-label="Admin menu" className="w-64 p-4 overflow-y-auto">
      {renderItems(items)}
    </nav>
  );
}
