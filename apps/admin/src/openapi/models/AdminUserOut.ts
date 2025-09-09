/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RestrictionOut } from './RestrictionOut';
export type AdminUserOut = {
  id: string;
  created_at: string;
  email?: string | null;
  wallet_address?: string | null;
  is_active: boolean;
  username?: string | null;
  bio?: string | null;
  avatar_url?: string | null;
  role: string;
  is_premium: boolean;
  premium_until?: string | null;
  restrictions?: Array<RestrictionOut>;
};
