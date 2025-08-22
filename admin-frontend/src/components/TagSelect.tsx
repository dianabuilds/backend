import TagInput from "./TagInput";

interface TagSelectProps {
  value?: string[];
  onChange?: (tags: string[]) => void;
  placeholder?: string;
}

export default function TagSelect({ value, onChange, placeholder }: TagSelectProps) {
  return <TagInput value={value} onChange={onChange} placeholder={placeholder} />;
}
