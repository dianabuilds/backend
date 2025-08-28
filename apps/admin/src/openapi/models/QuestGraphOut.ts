/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { QuestStep } from './QuestStep';
import type { QuestTransition } from './QuestTransition';
import type { QuestVersionOut } from './QuestVersionOut';
export type QuestGraphOut = {
    version: QuestVersionOut;
    steps?: Array<QuestStep>;
    transitions?: Array<QuestTransition>;
};

