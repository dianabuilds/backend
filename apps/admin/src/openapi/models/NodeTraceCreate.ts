/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTraceKind } from './NodeTraceKind';
import type { NodeTraceVisibility } from './NodeTraceVisibility';
export type NodeTraceCreate = {
    comment?: (string | null);
    kind: NodeTraceKind;
    node_id: string;
    tags?: Array<string>;
    visibility?: NodeTraceVisibility;
};

