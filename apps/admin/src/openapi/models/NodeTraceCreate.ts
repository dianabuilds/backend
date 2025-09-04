/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTraceKind } from './NodeTraceKind';
import type { NodeTraceVisibility } from './NodeTraceVisibility';
export type NodeTraceCreate = {
    node_id: string;
    kind: NodeTraceKind;
    comment?: (string | null);
    tags?: Array<string>;
    visibility?: NodeTraceVisibility;
};

