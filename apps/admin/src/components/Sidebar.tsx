import { useCallback, useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

import { type AdminMenuItem, getAdminMenu } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { getIconComponent } from "../icons/registry";
import { safeLocalStorage } from "../utils/safeStorage";

const defaultIcons: Record<string, string> = {
  dashboard: "home",
  "users-list": "users",
  nodes: "database",
  quests: "flag",
  navigation: "compass",
  "navigation-main": "compass",
  "nav-transitions": "shuffle",
  monitoring: "activity",
  traces: "search",
  content: "file",
  administration: "settings",
};

function useExpandedState() {
  const KEY = "adminSidebarExpanded";
  const [expanded, setExpanded] = useState<Record<string, boolean>>(() => {
    try {
      const raw = safeLocalStorage.getItem(KEY);
      return raw ? (JSON.parse(raw) as Record<string, boolean>) : {};
    } catch {
      return {};
    }
  });
  useEffect(() => {
    safeLocalStorage.setItem(KEY, JSON.stringify(expanded));
  }, [expanded]);
  const toggle = useCallback((id: string) => {
    setExpanded((s) => ({ ...s, [id]: !s[id] }));
  }, []);
  const setOpen = useCallback((id: string, val: boolean) => {
    setExpanded((s) => ({ ...s, [id]: val }));
  }, []);
  return { expanded, toggle, setOpen };
}

function useCollapsedState() {
  const KEY = "adminSidebarCollapsed";
  const [collapsed, setCollapsed] = useState<boolean>(() => {
    try {
      return safeLocalStorage.getItem(KEY) === "true";
    } catch {
      return false;
    }
  });
  useEffect(() => {
    safeLocalStorage.setItem(KEY, String(collapsed));
  }, [collapsed]);
  const toggle = useCallback(() => {
    setCollapsed((c) => !c);
  }, []);
  return { collapsed, toggle };
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
  collapsed,
}: {
  item: AdminMenuItem;
  level: number;
  activePath: string;
  expanded: Record<string, boolean>;
  toggle: (id: string) => void;
  collapsed: boolean;
}) {
  const Icon = getIconComponent(item.icon || defaultIcons[item.id]);

  const content = (
    <div className="flex items-center gap-2">
      <Icon className="w-4 h-4" aria-hidden />
      <span className={collapsed ? "sr-only" : ""}>{item.label}</span>
    </div>
  );

  if (item.divider) {
    return (
      <div role="separator" className="my-2 border-t border-gray-700" />
    );
  }

  const padding = collapsed ? 8 : 8 + level * 12;

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
            `block py-1 px-2 rounded hover:bg-gray-800 ${
              isActive || exact ? "font-semibold" : ""
            }`
          }
          style={{ paddingLeft: padding }}
          aria-current={isActive ? "page" : undefined}
          title={collapsed ? only.label : undefined}
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
          className={`w-full flex items-center justify-between text-left py-1 px-2 rounded hover:bg-gray-800 ${
            isActive ? "font-semibold" : ""
          }`}
          style={{ paddingLeft: padding }}
          onClick={() => toggle(item.id)}
          aria-expanded={open}
          aria-controls={`group-${item.id}`}
          title={collapsed ? item.label : undefined}
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
                collapsed={collapsed}
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
        className="block py-1 px-2 rounded hover:bg-gray-800"
        style={{ paddingLeft: padding }}
        title={collapsed ? item.label : undefined}
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
          `block py-1 px-2 rounded hover:bg-gray-800 ${
            isActive || exact ? "font-semibold" : ""
          }`
        }
        style={{ paddingLeft: padding }}
        aria-current={isActive ? "page" : undefined}
        title={collapsed ? item.label : undefined}
      >
        {content}
      </NavLink>
    );
  }

  return (
    <div
      className="py-1 px-2 text-gray-400"
      style={{ paddingLeft: padding }}
      title={collapsed ? item.label : undefined}
    >
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
  const { collapsed, toggle: toggleCollapsed } = useCollapsedState();
  const { user } = useAuth();

  const filterByRole = useCallback(
    (list: AdminMenuItem[]): AdminMenuItem[] => {
      const role = user?.role;
      return list
        .filter((i) => !i.roles || (role ? i.roles.includes(role) : false))
        .filter((i) => !i.hidden)
        .map((i) => ({
          ...i,
          children: i.children ? filterByRole(i.children) : [],
        }))
        .filter((i) => i.path || (i.children && i.children.length > 0));
    },
    [user?.role],
  );

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { items } = await getAdminMenu();
      // Доверяем порядку сервера: не пересортировываем на клиенте
      setItems(filterByRole([...items]));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems(null);
    } finally {
      setLoading(false);
    }
  }, [filterByRole]);

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
              className="h-4 bg-gray-800 rounded animate-pulse"
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
              className="block py-1 px-2 rounded hover:bg-gray-800"
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
            collapsed={collapsed}
          />
        ))}
      </nav>
    );
  }, [loading, error, items, location.pathname, expanded, toggle, collapsed]);

  const MenuIcon = getIconComponent("menu");

  return (
    <aside
      className={`${collapsed ? "w-16" : "w-64"} bg-gray-900 text-gray-100 p-4 shadow-sm`}
      aria-label="Sidebar navigation"
    >
      <button
        className="mb-4 p-2 rounded hover:bg-gray-800"
        onClick={toggleCollapsed}
        aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        aria-expanded={!collapsed}
      >
        <MenuIcon className="w-5 h-5" aria-hidden />
      </button>
      {content}
    </aside>
  );
}
