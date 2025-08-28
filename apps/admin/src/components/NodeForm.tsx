import EditorJSEmbed from "./EditorJSEmbed";
import FieldTitle from "./fields/FieldTitle";
import FieldTags from "./fields/FieldTags";
import FieldSummary from "./fields/FieldSummary";
import FieldMedia from "./fields/FieldMedia";
import type { OutputData } from "../types/editorjs";
import { useEffect, useId, useState, type Ref } from "react";
import { z } from "zod";

interface NodeFormProps {
  title: string;
  content: OutputData;
  tags: string[];
  media: string[];
  summary: string;
  onTitleChange: (value: string) => void;
  onContentChange: (data: OutputData) => void;
  onTagsChange: (tags: string[]) => void;
  onMediaChange: (media: string[]) => void;
  onSummaryChange: (value: string) => void;
  titleRef?: Ref<HTMLInputElement>;
}

export default function NodeForm({
  title,
  content,
  tags,
  media,
  summary,
  onTitleChange,
  onContentChange,
  onTagsChange,
  onMediaChange,
  onSummaryChange,
  titleRef,
}: NodeFormProps) {
  const contentId = useId();
  const contentDesc = `${contentId}-desc`;
  const [errors, setErrors] = useState<{
    tags: string | null;
    media: string | null;
    content: string | null;
  }>({ tags: null, media: null, content: null });

  const tagsSchema = z
    .array(z.string(), {
      invalid_type_error: "tags must be an array of strings",
    })
    .optional();
  const mediaSchema = z
    .array(z.string(), {
      invalid_type_error: "media must be an array of strings",
    })
    .optional();
  const contentSchema = z.any().superRefine((val, ctx) => {
    if (typeof val === "string") {
      try {
        JSON.parse(val);
      } catch {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "nodes must be valid JSON for Editor.js",
        });
        return;
      }
    }
    if (typeof val !== "object" || val === null) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: "nodes must be an object or array for Editor.js",
      });
    }
  });

  const handleTagsChange = (t: string[]) => {
    onTagsChange(t);
    validateTags(t);
  };

  const handleMediaChange = (m: string[]) => {
    onMediaChange(m);
    validateMedia(m);
  };

  const handleContentChange = (data: OutputData) => {
    onContentChange(data);
    validateContent(data);
  };

  const validateTags = (t: string[]) => {
    const res = tagsSchema.safeParse(t);
    setErrors((e) => ({ ...e, tags: res.success ? null : "tags must be an array of strings" }));
  };

  const validateMedia = (m: string[]) => {
    const res = mediaSchema.safeParse(m);
    setErrors((e) => ({ ...e, media: res.success ? null : "media must be an array of strings" }));
  };

  const validateContent = (data: OutputData) => {
    const res = contentSchema.safeParse(data);
    setErrors((e) => ({
      ...e,
      content: res.success ? null : res.error.errors[0]?.message || null,
    }));
  };

  // Initial validation
  useEffect(() => {
    validateTags(tags);
    validateMedia(media);
    validateContent(content);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
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
          <EditorJSEmbed
            value={content}
            onChange={handleContentChange}
            minHeight={400}
          />
        </div>
        {errors.content ? (
          <p id={contentDesc} className="mt-1 text-xs text-red-600">
            {errors.content}
          </p>
        ) : (
          <p id={contentDesc} className="mt-1 text-xs text-gray-600">
            Main body of the node with text and images.
          </p>
        )}
      </div>

      <div>
        <FieldTags
          value={tags}
          onChange={handleTagsChange}
          description="Add tags to help categorize the node."
          error={errors.tags}
        />
      </div>

      <div>
        <FieldMedia
          value={media}
          onChange={handleMediaChange}
          description="List of media URLs referenced by the node."
          placeholder="Add media URL and press Enter"
          error={errors.media}
        />
      </div>

      <FieldSummary value={summary} onChange={onSummaryChange} />
    </div>
  );
}

