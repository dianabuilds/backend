import EditorJSEmbed from "../EditorJSEmbed";
import type { OutputData } from "../../types/editorjs";

interface Props {
  value: OutputData;
  onChange?: (data: OutputData) => void;
}

export default function ContentTab({ value, onChange }: Props) {
  return <EditorJSEmbed value={value} onChange={onChange} />;
}
