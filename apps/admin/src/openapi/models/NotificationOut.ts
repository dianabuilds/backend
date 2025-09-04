/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { NotificationType } from './NotificationType';
export type NotificationOut = {
    id: string;
    title: string;
    message: string;
    created_at: string;
    read_at: (string | null);
    type: NotificationType;
    is_preview: boolean;
};

