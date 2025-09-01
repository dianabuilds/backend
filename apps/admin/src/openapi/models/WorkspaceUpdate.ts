/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceSettings_Input } from './WorkspaceSettings_Input';
import type { WorkspaceType } from './WorkspaceType';
export type WorkspaceUpdate = {
    name?: (string | null);
    slug?: (string | null);
    settings?: (WorkspaceSettings_Input | null);
    type?: (WorkspaceType | null);
    is_system?: (boolean | null);
};

