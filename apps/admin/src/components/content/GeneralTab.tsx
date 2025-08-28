import FieldTags from "../fields/FieldTags";
import FieldTitle from "../fields/FieldTitle";
import FieldCover from "../fields/FieldCover";
import FieldSummary from "../fields/FieldSummary";
import type { GeneralTabProps } from "./GeneralTab.helpers";

export default function GeneralTab({
  title,
  tags = [],
  isPublic = false,
  allowFeedback = true,
  premiumOnly = false,
  coverUrl = null,
  summary = "",
  titleError = null,
  summaryError = null,
  coverError = null,
  onTitleChange,
  titleRef,
  onTagsChange,
  onIsPublicChange,
  onAllowFeedbackChange,
  onPremiumOnlyChange,
  onCoverChange,
  onSummaryChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle
        ref={titleRef}
        value={title}
        onChange={onTitleChange}
        error={titleError}
      />
      {onSummaryChange ? (
        <FieldSummary
          value={summary}
          onChange={onSummaryChange}
          error={summaryError}
        />
      ) : null}
      {onCoverChange ? (
        <FieldCover value={coverUrl} onChange={onCoverChange} error={coverError} />
      ) : null}
      {onTagsChange ? <FieldTags value={tags} onChange={onTagsChange} /> : null}
      {onIsPublicChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => onIsPublicChange(e.target.checked)}
          />
          Published
        </label>
      ) : null}
      {onAllowFeedbackChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={allowFeedback}
            onChange={(e) => onAllowFeedbackChange(e.target.checked)}
          />
          Allow comments
        </label>
      ) : null}
      {onPremiumOnlyChange ? (
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={premiumOnly}
            onChange={(e) => onPremiumOnlyChange(e.target.checked)}
          />
          Premium only
        </label>
      ) : null}
    </div>
  );
}
