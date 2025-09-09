/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NodeTransitionType } from './NodeTransitionType';
import type { TransitionCondition } from './TransitionCondition';
export type NodeTransitionUpdate = {
  from_slug?: string | null;
  to_slug?: string | null;
  label?: string | null;
  type?: NodeTransitionType | null;
  condition?: TransitionCondition | null;
  weight?: number | null;
};
