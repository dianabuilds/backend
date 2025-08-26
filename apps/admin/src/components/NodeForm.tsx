import EditorJSEmbed from "./EditorJSEmbed";
import FieldTitle from "./fields/FieldTitle";
import FieldTags from "./fields/FieldTags";
import FieldSummary from "./fields/FieldSummary";
import type { OutputData } from "../types/editorjs";
import type { TagOut } from "./tags/TagPicker";
import { useId, type Ref } from "react";

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
  const contentId = useId();
  const contentDesc = `${contentId}-desc`;
  return (
    <div className="flex flex-col gap-4 p-3">
      <div>
        <FieldTitle
          ref={titleRef}
          value={title}
          onChange={onTitleChange}
          description="Short and descriptive title."
        />
      </div>

      <div>
        <label
          htmlFor={contentId}
          className="block text-sm font-medium text-gray-900"
        >
          Content
        </label>
        <div
          id={contentId}
          aria-describedby={contentDesc}
          className="mt-1"
        >
          <EditorJSEmbed value={content} onChange={onContentChange} />
        </div>
        <p id={contentDesc} className="mt-1 text-xs text-gray-600">
          Main body of the node with text and images.
        </p>
      </div>

      <div>
          <FieldTags
            value={tags}
            onChange={onTagsChange}
            description="Add tags to help categorize the node."
          />
      </div>

      <FieldSummary value={summary} onChange={onSummaryChange} />
    </div>
  );
}

