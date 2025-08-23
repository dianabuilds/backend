import type { TagOut } from "../tags/TagPicker";

export interface GeneralTabProps {
  title: string;
  slug: string;
  tags: TagOut[];
  cover: string | null;
  onTitleChange: (v: string) => void;
  onSlugChange: (v: string) => void;
  onTagsChange: (t: TagOut[]) => void;
  onCoverChange: (url: string | null) => void;
}
