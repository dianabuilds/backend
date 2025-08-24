import EditorJSEmbed from "../EditorJSEmbed";
import type { OutputData } from "../../types/editorjs";
import { useEditorNode } from "../../utils/useEditorNode";

interface Props {
  initial?: OutputData;
  onSave?: (data: OutputData) => Promise<void> | void;
}

export default function ContentTab({ initial, onSave }: Props) {
  const defaultData: OutputData =
    initial || ({ time: Date.now(), blocks: [], version: "2.30.7" } as OutputData);
  const { data, update } = useEditorNode<OutputData>(defaultData, onSave);
  return <EditorJSEmbed value={data} onChange={update} />;
}
