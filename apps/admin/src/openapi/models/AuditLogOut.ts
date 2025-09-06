/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AuditLogOut = {
    id: string;
    actor_id?: (string | null);
    action: string;
    resource_type?: (string | null);
    resource_id?: (string | null);
    account_id?: (string | null);
    before?: (Record<string, any> | null);
    after?: (Record<string, any> | null);
    ip?: (string | null);
    user_agent?: (string | null);
    created_at: string;
    extra?: (Record<string, any> | null);
};

