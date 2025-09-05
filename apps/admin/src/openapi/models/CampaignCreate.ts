/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CampaignFilters } from './CampaignFilters';
export type CampaignCreate = {
    title: string;
    message: string;
    type?: string;
    filters?: (CampaignFilters | null);
};
