/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
export type AdminTransitionOut = {
    id: string;
    from_slug: string;
    to_slug: string;
    type: NodeTransitionType;
    weight: number;
    label: (string | null);
    created_by: string;
    created_at: string;
};

