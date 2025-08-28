/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type QuestOut = {
    title?: (string | null);
    subtitle?: (string | null);
    description?: (string | null);
    cover_image?: (string | null);
    tags?: Array<string>;
    price?: (number | null);
    is_premium_only?: boolean;
    entry_node_id?: (string | null);
    nodes?: Array<string>;
    custom_transitions?: (Record<string, any> | null);
    allow_comments?: boolean;
    structure?: (string | null);
    length?: (string | null);
    tone?: (string | null);
    genre?: (string | null);
    locale?: (string | null);
    cost_generation?: (number | null);
    id: string;
    slug: string;
    author_id: string;
    is_draft: boolean;
    published_at: (string | null);
    created_at: string;
    created_by_user_id?: (string | null);
    updated_by_user_id?: (string | null);
};

