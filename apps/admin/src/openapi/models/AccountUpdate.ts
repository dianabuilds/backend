/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AccountSettings_Input } from './AccountSettings_Input';
import type { AccountType } from './AccountType';
export type AccountUpdate = {
    name?: (string | null);
    slug?: (string | null);
    settings?: (AccountSettings_Input | null);
    type?: (AccountType | null);
    is_system?: (boolean | null);
};

