/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
/**
 * Payload for bulk node admin operations.
 */
export type NodeBulkOperation = {
    ids: Array<number>;
    op: NodeBulkOperation.op;
};
export namespace NodeBulkOperation {
    export enum op {
        HIDE = 'hide',
        SHOW = 'show',
        TOGGLE_PREMIUM = 'toggle_premium',
        TOGGLE_RECOMMENDABLE = 'toggle_recommendable',
    }
}

