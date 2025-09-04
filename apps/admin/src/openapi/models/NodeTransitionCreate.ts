/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
import type { TransitionCondition } from './TransitionCondition';
export type NodeTransitionCreate = {
    to_slug: string;
    label?: (string | null);
    type?: NodeTransitionType;
    condition?: (TransitionCondition | null);
    weight?: number;
};

