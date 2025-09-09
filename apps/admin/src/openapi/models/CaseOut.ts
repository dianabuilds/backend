/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type CaseOut = {
  id: string;
  created_at: string;
  updated_at: string;
  type: string;
  status: string;
  priority: string;
  reporter_id?: string | null;
  reporter_contact?: string | null;
  target_type?: string | null;
  target_id?: string | null;
  summary: string;
  details?: string | null;
  assignee_id?: string | null;
  due_at?: string | null;
  first_response_due_at?: string | null;
  last_event_at?: string | null;
  source?: string | null;
  reason_code?: string | null;
  resolution?: string | null;
  labels?: Array<string>;
};
