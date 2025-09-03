/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
import type { TransitionCondition } from './TransitionCondition';
export type NodeTransitionCreate = {
    condition?: (TransitionCondition | null);
    label?: (string | null);
    to_slug: string;
    type?: NodeTransitionType;
    weight?: number;
};

