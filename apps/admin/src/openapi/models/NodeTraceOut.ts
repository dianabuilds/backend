/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTraceKind } from './NodeTraceKind';
import type { NodeTraceVisibility } from './NodeTraceVisibility';
import type { TraceUser } from './TraceUser';
export type NodeTraceOut = {
    comment?: (string | null);
    created_at: string;
    id: string;
    kind: NodeTraceKind;
    tags?: Array<string>;
    user?: (TraceUser | null);
    visibility: NodeTraceVisibility;
};

