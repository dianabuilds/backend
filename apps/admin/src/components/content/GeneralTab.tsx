import FieldTitle from "../fields/FieldTitle";
import FieldSlug from "../fields/FieldSlug";
import FieldTags from "../fields/FieldTags";
import FieldCover from "../fields/FieldCover";

export interface GeneralTabProps {
  title: string;
  slug: string;
  tags: string[];
  cover: string | null;
  onTitleChange: (v: string) => void;
  onSlugChange: (v: string) => void;
  onTagsChange: (t: string[]) => void;
  onCoverChange: (url: string | null) => void;
}

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
