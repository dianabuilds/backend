import EditorJSEmbed from "../EditorJSEmbed";
import type { OutputData } from "../../types/editorjs";
import { useAutosave } from "../../utils/useAutosave";

interface Props {
  initial?: OutputData;
  onSave?: (data: OutputData) => Promise<void> | void;
  storageKey?: string;
}

export default function ContentTab({ initial, onSave, storageKey }: Props) {
  const defaultData: OutputData =
    initial || ({ time: Date.now(), blocks: [], version: "2.30.7" } as OutputData);
  const { data, update } = useAutosave<OutputData>(
    defaultData,
    onSave,
    undefined,
    storageKey,
  );
  return <EditorJSEmbed value={data} onChange={update} />;
}
