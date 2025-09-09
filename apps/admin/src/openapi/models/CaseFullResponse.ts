/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { CaseAttachmentOut } from './CaseAttachmentOut';
import type { CaseEventOut } from './CaseEventOut';
import type { CaseNoteOut } from './CaseNoteOut';
import type { CaseOut } from './CaseOut';
export type CaseFullResponse = {
  case: CaseOut;
  notes: Array<CaseNoteOut>;
  attachments: Array<CaseAttachmentOut>;
  events: Array<CaseEventOut>;
};
