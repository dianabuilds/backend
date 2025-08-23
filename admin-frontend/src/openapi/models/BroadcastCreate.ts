/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { BroadcastFilters } from './BroadcastFilters';
export type BroadcastCreate = {
    title: string;
    message: string;
    type?: string;
    filters?: (BroadcastFilters | null);
    dry_run?: boolean;
};

