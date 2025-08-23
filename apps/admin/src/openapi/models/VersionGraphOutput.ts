/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { GraphEdgeOutput } from './GraphEdgeOutput';
import type { GraphNodeOutput } from './GraphNodeOutput';
import type { VersionSummaryOutput } from './VersionSummaryOutput';
export type VersionGraphOutput = {
    version: VersionSummaryOutput;
    nodes: Array<GraphNodeOutput>;
    edges: Array<GraphEdgeOutput>;
};

