/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { WorkspaceSettings_Input } from './WorkspaceSettings_Input';
import type { WorkspaceType } from './WorkspaceType';
export type WorkspaceIn = {
    is_system?: boolean;
    name: string;
    settings?: WorkspaceSettings_Input;
    slug?: (string | null);
    type?: WorkspaceType;
};

