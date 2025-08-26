import FieldTags from "../fields/FieldTags";
import FieldTitle from "../fields/FieldTitle";
import type { GeneralTabProps } from "./GeneralTab.helpers";

export default function GeneralTab({
  title,
  tags = [],
  is_public = false,
  allow_comments = true,
  is_premium_only = false,
  onTitleChange,
  onTagsChange,
  onIsPublicChange,
  onAllowCommentsChange,
  onPremiumOnlyChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle value={title} onChange={onTitleChange} />
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
