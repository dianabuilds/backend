/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type FeatureFlagOut = {
  key: string;
  value: boolean;
  audience: FeatureFlagOut.audience;
  description?: string | null;
  updated_at?: string | null;
  updated_by?: string | null;
};
export namespace FeatureFlagOut {
  export enum audience {
    ALL = 'all',
    PREMIUM = 'premium',
    BETA = 'beta',
  }
}
