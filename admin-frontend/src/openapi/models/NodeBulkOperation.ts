/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Payload for bulk node admin operations.
 */
export type NodeBulkOperation = {
    ids: Array<string>;
    op: 'hide' | 'show' | 'public' | 'private' | 'toggle_premium' | 'toggle_recommendable';
};

