import type { Ref } from "react";
export interface GeneralTabProps {
  title: string;
  tags?: string[];
  isPublic?: boolean;
  allowFeedback?: boolean;
  premiumOnly?: boolean;
  coverUrl?: string | null;
  summary?: string;
  titleError?: string | null;
  summaryError?: string | null;
  coverError?: string | null;
  onTitleChange: (v: string) => void;
  titleRef?: Ref<HTMLInputElement>;
  onTagsChange?: (tags: string[]) => void;
  onIsPublicChange?: (v: boolean) => void;
  onAllowFeedbackChange?: (v: boolean) => void;
  onPremiumOnlyChange?: (v: boolean) => void;
  onCoverChange?: (url: string | null) => void;
  onSummaryChange?: (v: string) => void;
  [key: string]: unknown;
}
