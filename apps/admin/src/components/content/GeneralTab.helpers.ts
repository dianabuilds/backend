import type { Ref } from "react";
export interface GeneralTabProps {
  title: string;
  tags?: string[];
  is_public?: boolean;
  allow_comments?: boolean;
  is_premium_only?: boolean;
  cover_url?: string | null;
  summary?: string;
  titleError?: string | null;
  summaryError?: string | null;
  coverError?: string | null;
  onTitleChange: (v: string) => void;
  titleRef?: Ref<HTMLInputElement>;
  onTagsChange?: (tags: string[]) => void;
  onIsPublicChange?: (v: boolean) => void;
  onAllowCommentsChange?: (v: boolean) => void;
  onPremiumOnlyChange?: (v: boolean) => void;
  onCoverChange?: (url: string | null) => void;
  onSummaryChange?: (v: string) => void;
  [key: string]: unknown;
}
