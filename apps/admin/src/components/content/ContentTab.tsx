import type { OutputData } from '../../types/editorjs';
import EditorJSEmbed from '../EditorJSEmbed';

interface Props {
  value: OutputData;
  onChange?: (data: OutputData) => void;
}

export default function ContentTab({ value, onChange }: Props) {
  return <EditorJSEmbed value={value} onChange={onChange} />;
}
