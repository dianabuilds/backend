export interface GeneralTabProps {
  title: string;
  allow_comments: boolean;
  is_premium_only: boolean;
  onTitleChange: (v: string) => void;
  onAllowCommentsChange: (v: boolean) => void;
  onPremiumOnlyChange: (v: boolean) => void;
}
