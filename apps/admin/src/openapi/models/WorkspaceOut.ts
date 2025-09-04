/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceRole } from './WorkspaceRole';
import type { WorkspaceSettings_Output } from './WorkspaceSettings_Output';
import type { WorkspaceType } from './WorkspaceType';
export type WorkspaceOut = {
    id: string;
    name: string;
    slug: string;
    owner_user_id: string;
    settings_json?: WorkspaceSettings_Output;
    type: WorkspaceType;
    is_system: boolean;
    created_at: string;
    updated_at: string;
    role?: (WorkspaceRole | null);
};

