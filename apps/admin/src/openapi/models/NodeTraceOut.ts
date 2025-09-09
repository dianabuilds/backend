/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTraceKind } from './NodeTraceKind';
import type { NodeTraceVisibility } from './NodeTraceVisibility';
import type { TraceUser } from './TraceUser';
export type NodeTraceOut = {
  id: string;
  created_at: string;
  user?: TraceUser | null;
  kind: NodeTraceKind;
  comment?: string | null;
  tags?: Array<string>;
  visibility: NodeTraceVisibility;
};
