/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AuditLogOut = {
    action: string;
    actor_id?: (string | null);
    after?: (Record<string, any> | null);
    before?: (Record<string, any> | null);
    created_at: string;
    extra?: (Record<string, any> | null);
    id: string;
    ip?: (string | null);
    resource_id?: (string | null);
    resource_type?: (string | null);
    user_agent?: (string | null);
    workspace_id?: (string | null);
};

