import EditorJSEmbed from "./EditorJSEmbed";
import FieldTitle from "./fields/FieldTitle";
import FieldTags from "./fields/FieldTags";
import FieldSummary from "./fields/FieldSummary";
import type { OutputData } from "../types/editorjs";
import type { TagOut } from "./tags/TagPicker";
import type { Ref } from "react";

interface NodeFormProps {
  title: string;
  content: OutputData;
  tags: TagOut[];
  summary: string;
  onTitleChange: (value: string) => void;
  onContentChange: (data: OutputData) => void;
  onTagsChange: (tags: TagOut[]) => void;
  onSummaryChange: (value: string) => void;
  titleRef?: Ref<HTMLInputElement>;
}

export default function NodeForm({
  title,
  content,
  tags,
  summary,
  onTitleChange,
  onContentChange,
  onTagsChange,
  onSummaryChange,
  titleRef,
}: NodeFormProps) {
  return (
    <div className="flex flex-col gap-4 p-3">
      <div>
        <FieldTitle ref={titleRef} value={title} onChange={onTitleChange} />
        <p className="mt-1 text-xs text-gray-500">
          Short and descriptive title.
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium">Content</label>
        <EditorJSEmbed value={content} onChange={onContentChange} />
        <p className="mt-1 text-xs text-gray-500">
          Main body of the node with text and images.
        </p>
      </div>

      <div>
        <FieldTags value={tags} onChange={onTagsChange} />
        <p className="mt-1 text-xs text-gray-500">
          Add tags to help categorize the node.
        </p>
      </div>

      <FieldSummary value={summary} onChange={onSummaryChange} />
    </div>
  );
}

