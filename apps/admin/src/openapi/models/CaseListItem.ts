/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CaseListItem = {
    id: string;
    type: string;
    status: string;
    priority: string;
    summary: string;
    target_type?: (string | null);
    target_id?: (string | null);
    assignee_id?: (string | null);
    labels?: Array<string>;
    created_at: string;
    due_at?: (string | null);
    last_event_at?: (string | null);
};

