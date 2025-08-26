import {
  Activity,
  CreditCard,
  Ban,
  Bell,
  Box,
  Database,
  Flag,
  ExternalLink,
  FileText,
  Home,
  Menu as MenuIcon,
  Lock,
  Search,
  Settings,
  Shield,
  Tag,
  Trophy,
  Plug,
  Users as UsersIcon,
} from "lucide-react";
import type React from "react";

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
  | "notifications"
  | "lock"
  | "credit-card"
  | "plug"
  | "flag";

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
  achievements: Trophy,
  notifications: Bell,
  lock: Lock,
  "credit-card": CreditCard,
  plug: Plug,
  flag: Flag,
};

export function getIconComponent(
  name?: string | null,
): React.ComponentType<any> {
  if (!name) return MenuIcon;
  return iconRegistry[name] || MenuIcon;
}
