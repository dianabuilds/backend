import {
  Activity,
  Ban,
  Bell,
  Box,
  Compass,
  CreditCard,
  Database,
  ExternalLink,
  FileText,
  Flag,
  Home,
  Lock,
  Menu as MenuIcon,
  Plug,
  Search,
  Settings,
  Shield,
  Shuffle,
  Tag,
  Trophy,
  Users as UsersIcon,
} from 'lucide-react';
import type React from 'react';

export type IconName =
  | 'home'
  | 'users'
  | 'activity'
  | 'file'
  | 'ban'
  | 'settings'
  | 'shield'
  | 'tag'
  | 'search'
  | 'external'
  | 'menu'
  | 'database'
  | 'box'
  | 'bell'
  | 'notifications'
  | 'lock'
  | 'credit-card'
  | 'plug'
  | 'flag'
  | 'compass'
  | 'shuffle';

const iconRegistry: Record<string, React.ComponentType<React.SVGProps<SVGSVGElement>>> = {
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
  'credit-card': CreditCard,
  plug: Plug,
  flag: Flag,
  compass: Compass,
  shuffle: Shuffle,
};

export function getIconComponent(
  name?: string | null,
): React.ComponentType<React.SVGProps<SVGSVGElement>> {
  if (!name) return MenuIcon;
  return iconRegistry[name] || MenuIcon;
}
