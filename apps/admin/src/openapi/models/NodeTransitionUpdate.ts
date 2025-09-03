/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
import type { TransitionCondition } from './TransitionCondition';
export type NodeTransitionUpdate = {
    condition?: (TransitionCondition | null);
    from_slug?: (string | null);
    label?: (string | null);
    to_slug?: (string | null);
    type?: (NodeTransitionType | null);
    weight?: (number | null);
};

