import type {
  DrawerTabKey,
  FilterState,
  RoleFilterValue,
  SortState,
  StatusFilterValue,
} from './types';

export const STATUS_FILTERS: Array<{ value: StatusFilterValue; label: string }> = [
  { value: 'all', label: 'All statuses' },
  { value: 'active', label: 'Active' },
  { value: 'pending', label: 'Pending' },
  { value: 'banned', label: 'Banned' },
  { value: 'review', label: 'Needs review' },
];

export const ROLE_FILTERS: Array<{ value: RoleFilterValue; label: string; description: string }> = [
  { value: 'any', label: 'Any role', description: 'Show users across all access levels.' },
  { value: 'admin', label: 'Admin', description: 'Full platform access.' },
  { value: 'moderator', label: 'Moderator', description: 'Moderation and enforcement tools.' },
  { value: 'support', label: 'Support', description: 'Support workflows and ticketing.' },
  { value: 'user', label: 'User', description: 'Regular member without elevated access.' },
];

export const RISK_FILTERS: Array<{ value: FilterState['risk']; label: string }> = [
  { value: 'any', label: 'Any risk' },
  { value: 'high', label: 'High risk' },
  { value: 'medium', label: 'Medium risk' },
  { value: 'low', label: 'Low risk' },
];

// backend currently applies logic only for these sanction types
export const SANCTION_TYPES = ['ban', 'warning'];

export const DRAWER_TABS: Array<{ key: DrawerTabKey; label: string }> = [
  { key: 'overview', label: 'Overview' },
  { key: 'roles', label: 'Roles' },
  { key: 'sanctions', label: 'Sanctions' },
  { key: 'notes', label: 'Notes' },
  { key: 'activity', label: 'Activity' },
];

export const DEFAULT_FILTERS: FilterState = {
  status: 'all',
  role: 'any',
  risk: 'any',
  registrationFrom: '',
  registrationTo: '',
};

export const DEFAULT_SORT: SortState = { key: 'registered_at', order: 'desc' };

export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

