/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GraphEdgeInput } from './GraphEdgeInput';
import type { GraphNodeInput } from './GraphNodeInput';
import type { VersionSummaryInput } from './VersionSummaryInput';
export type VersionGraphInput = {
    version: VersionSummaryInput;
    nodes: Array<GraphNodeInput>;
    edges: Array<GraphEdgeInput>;
};

