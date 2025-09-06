/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { AccountSettings_Input } from './AccountSettings_Input';
import type { AccountType } from './AccountType';
export type AccountIn = {
    name: string;
    slug?: (string | null);
    settings?: AccountSettings_Input;
    type?: AccountType;
    is_system?: boolean;
};

