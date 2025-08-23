export interface GeneralTabProps {
  title: string;
  slug: string;
  tags: string[];
  cover: string | null;
  onTitleChange: (v: string) => void;
  onSlugChange: (v: string) => void;
  onTagsChange: (t: string[]) => void;
  onCoverChange: (url: string | null) => void;
}
