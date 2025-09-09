/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type SchedulePublishIn = {
  run_at: string;
  access?: SchedulePublishIn.access;
};
export namespace SchedulePublishIn {
  export enum access {
    EVERYONE = 'everyone',
    PREMIUM_ONLY = 'premium_only',
    EARLY_ACCESS = 'early_access',
  }
}
