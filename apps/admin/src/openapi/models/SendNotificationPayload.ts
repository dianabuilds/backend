/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NotificationType } from './NotificationType';
export type SendNotificationPayload = {
    message: string;
    title: string;
    type?: NotificationType;
    user_id: string;
    workspace_id: string;
};

