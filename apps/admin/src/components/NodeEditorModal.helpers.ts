export interface NodeEditorData {
  id: string;
  title: string;
  subtitle?: string;
  cover_url?: string | null;
  tags?: string[];
  allow_comments?: boolean;
  is_premium_only?: boolean;
  contentData: any;
}
