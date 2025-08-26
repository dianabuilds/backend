import FieldTags from "../fields/FieldTags";
import FieldTitle from "../fields/FieldTitle";
import FieldCover from "../fields/FieldCover";
import FieldSummary from "../fields/FieldSummary";
import type { GeneralTabProps } from "./GeneralTab.helpers";

export default function GeneralTab({
  title,
  tags = [],
  is_public = false,
  allow_comments = true,
  is_premium_only = false,
  cover_url = null,
  summary = "",
  onTitleChange,
  titleRef,
  onTagsChange,
  onIsPublicChange,
  onAllowCommentsChange,
  onPremiumOnlyChange,
  onCoverChange,
  onSummaryChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle ref={titleRef} value={title} onChange={onTitleChange} />
      {onSummaryChange ? (
        <FieldSummary value={summary} onChange={onSummaryChange} />
      ) : null}
      {onCoverChange ? (
        <FieldCover value={cover_url} onChange={onCoverChange} />
      ) : null}
      {onTagsChange ? <FieldTags value={tags} onChange={onTagsChange} /> : null}
      {onIsPublicChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={is_public}
            onChange={(e) => onIsPublicChange(e.target.checked)}
          />
          Published
        </label>
      ) : null}
      {onAllowCommentsChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={allow_comments}
            onChange={(e) => onAllowCommentsChange(e.target.checked)}
          />
          Allow comments
        </label>
      ) : null}
      {onPremiumOnlyChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={is_premium_only}
            onChange={(e) => onPremiumOnlyChange(e.target.checked)}
          />
          Premium only
        </label>
      ) : null}
    </div>
  );
}
