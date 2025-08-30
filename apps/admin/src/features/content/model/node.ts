import type { OutputData } from "../../types/editorjs";

export interface NodeEditorData {
  id?: string;
  title: string;
  slug?: string;
  content: OutputData;
  coverUrl?: string | null;
  tags: string[];
  isPublic: boolean;
  premiumOnly: boolean;
  allowComments: boolean;
}
