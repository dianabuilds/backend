import FieldCover from "../fields/FieldCover";
import FieldSlug from "../fields/FieldSlug";
import FieldTags from "../fields/FieldTags";
import FieldTitle from "../fields/FieldTitle";
import type { GeneralTabProps } from "./GeneralTab.helpers";

export default function GeneralTab({
  title,
  slug,
  tags,
  cover,
  onTitleChange,
  onSlugChange,
  onTagsChange,
  onCoverChange,
}: GeneralTabProps) {
  return (
    <div className="space-y-4">
      <FieldTitle value={title} onChange={onTitleChange} />
      <FieldSlug value={slug} onChange={onSlugChange} />
      <FieldTags value={tags} onChange={onTagsChange} />
      <FieldCover value={cover} onChange={onCoverChange} />
    </div>
  );
}
