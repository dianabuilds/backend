/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceSettings_Input } from './WorkspaceSettings_Input';
import type { WorkspaceType } from './WorkspaceType';
export type WorkspaceIn = {
    name: string;
    slug?: (string | null);
    settings?: WorkspaceSettings_Input;
    type?: WorkspaceType;
    is_system?: boolean;
};

