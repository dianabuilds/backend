/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type RestrictionAdminCreate = {
    expires_at?: (string | null);
    reason?: (string | null);
    type: RestrictionAdminCreate.type;
    user_id: string;
};
export namespace RestrictionAdminCreate {
    export enum type {
        BAN = 'ban',
        POST_RESTRICT = 'post_restrict',
    }
}

