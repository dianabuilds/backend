/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type GenerationJobOut = {
    id: string;
    status: string;
    created_at: string;
    started_at?: (string | null);
    finished_at?: (string | null);
    created_by?: (string | null);
    provider?: (string | null);
    model?: (string | null);
    params: Record<string, any>;
    result_quest_id?: (string | null);
    result_version_id?: (string | null);
    cost?: (number | null);
    token_usage?: (Record<string, any> | null);
    reused?: boolean;
    progress?: number;
    logs?: null;
    error?: (string | null);
};

