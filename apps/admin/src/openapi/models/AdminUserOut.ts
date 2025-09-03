/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { RestrictionOut } from './RestrictionOut';
export type AdminUserOut = {
    avatar_url?: (string | null);
    bio?: (string | null);
    created_at: string;
    email?: (string | null);
    id: string;
    is_active: boolean;
    is_premium: boolean;
    premium_until?: (string | null);
    restrictions?: Array<RestrictionOut>;
    role: string;
    username?: (string | null);
    wallet_address?: (string | null);
};

