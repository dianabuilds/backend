/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
export type AdminTransitionOut = {
    created_at: string;
    created_by: string;
    from_slug: string;
    id: string;
    label: (string | null);
    to_slug: string;
    type: NodeTransitionType;
    weight: number;
};

