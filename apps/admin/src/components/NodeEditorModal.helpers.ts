import type { TagOut } from "./tags/TagPicker";
import type { OutputData } from "../types/editorjs";

export interface NodeEditorData {
  id: string;
  title: string;
  subtitle?: string;
  cover_url?: string | null;
  tags?: TagOut[];
  allow_comments?: boolean;
  is_premium_only?: boolean;
  contentData: OutputData;
}
