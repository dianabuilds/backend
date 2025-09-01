/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type PublishIn = {
    access?: PublishIn.access;
    cover?: (string | null);
};
export namespace PublishIn {
    export enum access {
        EVERYONE = 'everyone',
        PREMIUM_ONLY = 'premium_only',
        EARLY_ACCESS = 'early_access',
    }
}

