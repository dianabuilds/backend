import TagSelect from "../TagSelect";

interface Props {
  value: string[];
  onChange: (tags: string[]) => void;
}

export default function FieldTags({ value, onChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium">Tags</label>
      <TagSelect value={value} onChange={onChange} />
    </div>
  );
}
