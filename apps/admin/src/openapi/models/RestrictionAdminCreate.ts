/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RestrictionAdminCreate = {
  user_id: string;
  type: RestrictionAdminCreate.type;
  reason?: string | null;
  expires_at?: string | null;
};
export namespace RestrictionAdminCreate {
  export enum type {
    BAN = 'ban',
    POST_RESTRICT = 'post_restrict',
  }
}
