/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CaseAttachmentCreate } from './CaseAttachmentCreate';
export type CaseCreate = {
  type: string;
  summary: string;
  details?: string | null;
  target_type?: string | null;
  target_id?: string | null;
  reporter_id?: string | null;
  reporter_contact?: string | null;
  priority?: string | null;
  labels?: Array<string> | null;
  assignee_id?: string | null;
  attachments?: Array<CaseAttachmentCreate> | null;
};
