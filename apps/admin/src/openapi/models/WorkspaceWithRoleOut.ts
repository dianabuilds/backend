/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceRole } from './WorkspaceRole';
import type { WorkspaceSettings_Output } from './WorkspaceSettings_Output';
import type { WorkspaceType } from './WorkspaceType';
export type WorkspaceWithRoleOut = {
    created_at: string;
    id: string;
    is_system: boolean;
    name: string;
    owner_user_id: string;
    role: WorkspaceRole;
    settings_json?: WorkspaceSettings_Output;
    slug: string;
    type: WorkspaceType;
    updated_at: string;
};

