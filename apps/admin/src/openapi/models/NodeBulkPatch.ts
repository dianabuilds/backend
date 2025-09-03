/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeBulkPatchChanges } from './NodeBulkPatchChanges';
/**
 * Payload for bulk node patch operations.
 */
export type NodeBulkPatch = {
    changes: NodeBulkPatchChanges;
    ids: Array<number>;
};

