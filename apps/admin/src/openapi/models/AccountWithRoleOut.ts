/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AccountRole } from './AccountRole';
import type { AccountSettings_Output } from './AccountSettings_Output';
import type { AccountType } from './AccountType';
export type AccountWithRoleOut = {
    id: string;
    name: string;
    slug: string;
    owner_user_id: string;
    settings_json?: AccountSettings_Output;
    type: AccountType;
    is_system: boolean;
    created_at: string;
    updated_at: string;
    role: AccountRole;
};

