import MediaPicker from "../MediaPicker";

interface Props {
  value: string | null;
  onChange: (url: string | null) => void;
}

export default function FieldCover({ value, onChange }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium">Cover</label>
      <MediaPicker value={value} onChange={onChange} />
    </div>
  );
}
