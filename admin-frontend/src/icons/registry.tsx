import React from "react";
import {
  Home,
  Users as UsersIcon,
  Activity,
  FileText,
  Ban,
  Settings,
  Shield,
  Tag,
  Search,
  ExternalLink,
  Menu as MenuIcon,
  Database,
  Box,
  Bell,
} from "lucide-react";

export type IconName =
  | "home"
  | "users"
  | "activity"
  | "file"
  | "ban"
  | "settings"
  | "shield"
  | "tag"
  | "search"
  | "external"
  | "menu"
  | "database"
  | "box"
  | "bell"
  | "notifications";

export const iconRegistry: Record<string, React.ComponentType<any>> = {
  home: Home,
  users: UsersIcon,
  activity: Activity,
  file: FileText,
  ban: Ban,
  settings: Settings,
  shield: Shield,
  tag: Tag,
  search: Search,
  external: ExternalLink,
  menu: MenuIcon,
  database: Database,
  box: Box,
  bell: Bell,
  notifications: Bell,
};

export function getIconComponent(name?: string | null): React.ComponentType<any> {
  if (!name) return MenuIcon;
  return iconRegistry[name] || MenuIcon;
}
