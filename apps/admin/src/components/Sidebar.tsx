import { useCallback, useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { type AdminMenuItem, getAdminMenu } from "../api/client";
import { getIconComponent } from "../icons/registry";

function useExpandedState() {
  const KEY = "adminSidebarExpanded";
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    try {
      const raw = localStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as Record<string, boolean>) : {};
    } catch {
      return {};
    }
  });
  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(expanded));
  }, [expanded]);
  const toggle = useCallback((id: string) => {
    setExpanded((s) => ({ ...s, [id]: !s[id] }));
  }, []);
  const setOpen = useCallback((id: string, val: boolean) => {
    setExpanded((s) => ({ ...s, [id]: val }));
  }, []);
  return { expanded, toggle, setOpen };
}

/**
 * Приводит путь из меню к виду, совместимому с Router basename.
 * - Из абсолютного URL берёт pathname
 * - Удаляет префикс "/admin" или "/admin/" если он есть
 * - Преобразует "/admin" в "/" (корень админки)
 */
function normalizePath(p?: string | null): string | null {
  if (!p) return null;
  let path = p;
  try {
    // Если пришёл абсолютный URL, извлечём pathname
    const url = new URL(p, window.location.origin);
    path = url.pathname;
  } catch {
    // p уже относительный путь — ок
  }
  if (path === "/admin") return "/";
  if (path.startsWith("/admin/")) return path.slice("/admin".length);
  return path;
}

function longestPrefixMatch(
  pathname: string,
  itemPath?: string | null,
): boolean {
  if (!itemPath) return false;
  // Ensure trailing slash consistency for matching prefixes
  const a = pathname.endsWith("/") ? pathname : pathname + "/";
  const b = itemPath.endsWith("/") ? itemPath : itemPath + "/";
  return a.startsWith(b);
}

function MenuItem({
  item,
  level,
  activePath,
  expanded,
  toggle,
}: {
  item: AdminMenuItem;
  level: number;
  activePath: string;
  expanded: Record<string, boolean>;
  toggle: (id: string) => void;
}) {
  const Icon = getIconComponent(item.icon);

  const content = (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4" aria-hidden />
      <span>{item.label}</span>
    </div>
  );

  if (item.divider) {
    return (
      <div
        role="separator"
        className="my-2 border-t border-gray-200 dark:border-gray-700"
      />
    );
  }

  const padding = 8 + level * 12;

  if (item.children && item.children.length > 0) {
    // Если только один дочерний элемент и у родителя нет собственного path —
    // делаем верхний пункт ссылкой на ребенка (компактный режим).
    if ((!item.path || item.path === null) && item.children.length === 1) {
      const only = item.children[0] as AdminMenuItem;
      const to = normalizePath(only.path) || "/";
      const isActive = longestPrefixMatch(activePath, to);
      return (
        <NavLink
          to={to}
          className={({ isActive: exact }) =>
            `block py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 ${isActive || exact ? "font-semibold" : ""}`
          }
          style={{ paddingLeft: padding }}
          aria-current={isActive ? "page" : undefined}
        >
          {content}
        </NavLink>
      );
    }

    const open = expanded[item.id] ?? false;
    // Auto-open if a child is active
    const childActive = item.children.some((c: AdminMenuItem) =>
      longestPrefixMatch(activePath, normalizePath(c.path) || undefined),
    );
    const isActive =
      longestPrefixMatch(activePath, normalizePath(item.path) || undefined) ||
      childActive;

    useEffect(() => {
      if (childActive && !open) {
        toggle(item.id);
      }
    }, [childActive, open, toggle, item.id]);

    return (
      <div>
        <button
          className={`w-full flex items-center justify-between text-left py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 ${
            isActive ? "font-semibold" : ""
          }`}
          style={{ paddingLeft: padding }}
          onClick={() => toggle(item.id)}
          aria-expanded={open}
          aria-controls={`group-${item.id}`}
        >
          {content}
          <span aria-hidden>{open ? "▾" : "▸"}</span>
        </button>
        {open && (
          <div id={`group-${item.id}`} className="mt-1 space-y-1">
            {item.children.map((child: AdminMenuItem) => (
              <MenuItem
                key={child.id}
                item={child}
                level={level + 1}
                activePath={activePath}
                expanded={expanded}
                toggle={toggle}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (item.external && item.path) {
    return (
      <a
        href={item.path}
        target="_blank"
        rel="noreferrer"
        className="block py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
        style={{ paddingLeft: padding }}
      >
        {content}
      </a>
    );
  }

  if (item.path) {
    const to = normalizePath(item.path) || "/";
    const isActive = longestPrefixMatch(activePath, to);
    return (
      <NavLink
        to={to}
        className={({ isActive: exact }) =>
          `block py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800 ${isActive || exact ? "font-semibold" : ""}`
        }
        style={{ paddingLeft: padding }}
        aria-current={isActive ? "page" : undefined}
      >
        {content}
      </NavLink>
    );
  }

  return (
    <div className="py-1 px-2 text-gray-500" style={{ paddingLeft: padding }}>
      {content}
    </div>
  );
}

export default function Sidebar() {
  const location = useLocation();
  const [items, setItems] = useState<AdminMenuItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { expanded, toggle } = useExpandedState();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { items } = await getAdminMenu();
      const list = [...items];
      const preview: AdminMenuItem = {
        id: "preview",
        label: "Preview",
        path: "/preview",
        icon: "activity",
      };
      let placed = false;
      for (const section of list) {
        if (section.id === "navigation") {
          section.children = section.children || [];
          if (!section.children.some((c) => c.id === preview.id)) {
            section.children.push(preview);
          }
          placed = true;
          break;
        }
      }
      if (!placed && !list.some((i) => i.id === preview.id)) {
        list.push(preview);
      }
      const traceItem: AdminMenuItem = {
        id: "transitions-trace",
        label: "Transitions Trace",
        path: "/transitions/trace",
        icon: "activity",
      };
      if (!list.some((i) => i.id === traceItem.id)) {
        const idx = list.findIndex((i) => i.id === "transitions");
        if (idx >= 0) {
          list.splice(idx + 1, 0, traceItem);
        } else {
          list.push(traceItem);
        }
      }
      // Доверяем порядку сервера: не пересортировываем на клиенте
      setItems(list);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const content = useMemo(() => {
    if (loading) {
      // Skeleton
      return (
        <div className="space-y-2" aria-busy>
          {Array.from({ length: 6 }).map((_, i) => (
            <div
              key={i}
              className="h-4 bg-gray-200 dark:bg-gray-800 rounded animate-pulse"
            />
          ))}
        </div>
      );
    }
    if (error) {
      // Fallback minimal menu
      return (
        <div>
          <div className="mb-2 text-sm text-red-600" role="alert">
            {error}
          </div>
          <nav className="space-y-1">
            <NavLink
              to="/"
              className="block py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-800"
            >
              Dashboard
            </NavLink>
          </nav>
        </div>
      );
    }
    return (
      <nav className="space-y-1">
        {(items || []).map((item) => (
          <MenuItem
            key={item.id}
            item={item}
            level={0}
            activePath={location.pathname}
            expanded={expanded}
            toggle={toggle}
          />
        ))}
      </nav>
    );
  }, [loading, error, items, location.pathname, expanded, toggle]);

  return (
    <aside
      className="w-64 bg-white dark:bg-gray-900 p-4 shadow-sm"
      aria-label="Sidebar navigation"
    >
      {content}
    </aside>
  );
}
