import TagPicker, { type TagOut } from "../tags/TagPicker";

interface Props {
  value: TagOut[];
  onChange: (tags: TagOut[]) => void;
}

export default function FieldTags({ value, onChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium">Tags</label>
      <TagPicker value={value} onChange={onChange} />
    </div>
  );
}
