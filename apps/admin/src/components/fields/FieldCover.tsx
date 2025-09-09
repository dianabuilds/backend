import MediaPicker from '../MediaPicker';

interface Props {
  value?: string | null;
  onChange?: (url: string | null) => void;
  error?: string | null;
}

export default function FieldCover({ value = null, onChange, error }: Props) {
  return (
    <div>
      <label className="block text-sm font-medium">Cover</label>
      <MediaPicker value={value} onChange={onChange} />
      {error ? <p className="mt-1 text-xs text-red-600">{error}</p> : null}
    </div>
  );
}
