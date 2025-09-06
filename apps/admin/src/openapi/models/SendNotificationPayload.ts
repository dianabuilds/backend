/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NotificationType } from './NotificationType';
export type SendNotificationPayload = {
    account_id: string;
    user_id: string;
    title: string;
    message: string;
    type?: NotificationType;
};

