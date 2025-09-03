/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type NavigationCacheInvalidateRequest = {
    node_slug?: (string | null);
    scope: NavigationCacheInvalidateRequest.scope;
    user_id?: (string | null);
};
export namespace NavigationCacheInvalidateRequest {
    export enum scope {
        NODE = 'node',
        USER = 'user',
        ALL = 'all',
    }
}

