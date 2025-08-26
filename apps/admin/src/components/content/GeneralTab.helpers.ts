import type { TagOut } from "../tags/TagPicker";

export interface GeneralTabProps {
  title: string;
  tags?: TagOut[];
  is_public?: boolean;
  allow_comments?: boolean;
  is_premium_only?: boolean;
  cover_url?: string | null;
  summary?: string;
  onTitleChange: (v: string) => void;
  onTagsChange?: (tags: TagOut[]) => void;
  onIsPublicChange?: (v: boolean) => void;
  onAllowCommentsChange?: (v: boolean) => void;
  onPremiumOnlyChange?: (v: boolean) => void;
  onCoverChange?: (url: string | null) => void;
  onSummaryChange?: (v: string) => void;
  [key: string]: unknown;
}
