/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BroadcastFilters } from './BroadcastFilters';
export type BroadcastCreate = {
    dry_run?: boolean;
    filters?: (BroadcastFilters | null);
    message: string;
    title: string;
    type?: string;
};

