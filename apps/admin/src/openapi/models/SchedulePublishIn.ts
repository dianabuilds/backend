/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SchedulePublishIn = {
    access?: SchedulePublishIn.access;
    run_at: string;
};
export namespace SchedulePublishIn {
    export enum access {
        EVERYONE = 'everyone',
        PREMIUM_ONLY = 'premium_only',
        EARLY_ACCESS = 'early_access',
    }
}

