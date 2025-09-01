export interface NodeEditorData {
  id?: number;
  title: string;
  slug?: string;
  coverUrl?: string | null;
  media?: string[];
  tags?: string[];
  // additional fields used by the redesigned editor
  isPublic?: boolean;
  content?: any;
}
