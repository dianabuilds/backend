/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceRole } from './WorkspaceRole';
export type WorkspaceOut = {
    id: string;
    name: string;
    slug: string;
    owner_user_id: string;
    settings: Record<string, any>;
    created_at: string;
    updated_at: string;
    role?: WorkspaceRole;
};

