import FieldTitle from "../fields/FieldTitle";
import type { GeneralTabProps } from "./GeneralTab.helpers";

export default function GeneralTab({
  title,
  onTitleChange,
  allow_comments,
  is_premium_only,
  onAllowCommentsChange,
  onPremiumOnlyChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle value={title} onChange={onTitleChange} />
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={allow_comments}
          onChange={(e) => onAllowCommentsChange(e.target.checked)}
        />
        Allow comments
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          checked={is_premium_only}
          onChange={(e) => onPremiumOnlyChange(e.target.checked)}
        />
        Premium only
      </label>
    </div>
  );
}
