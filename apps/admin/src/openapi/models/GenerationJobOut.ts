/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type GenerationJobOut = {
    cost?: (number | null);
    created_at: string;
    created_by?: (string | null);
    error?: (string | null);
    finished_at?: (string | null);
    id: string;
    logs?: null;
    model?: (string | null);
    params: Record<string, any>;
    progress?: number;
    provider?: (string | null);
    result_quest_id?: (string | null);
    result_version_id?: (string | null);
    reused?: boolean;
    started_at?: (string | null);
    status: string;
    token_usage?: (Record<string, any> | null);
};

