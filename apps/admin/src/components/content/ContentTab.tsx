import type { OutputData } from '../../types/editorjs';
import EditorJSEmbed from '../EditorJSEmbed';

interface Props {
  value?: OutputData;
  initial?: OutputData;
  onChange?: (data: OutputData) => void;
}

export default function ContentTab({ value, initial, onChange }: Props) {
  return <EditorJSEmbed value={value ?? initial} onChange={onChange} />;
}
