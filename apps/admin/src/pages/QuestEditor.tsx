import { useState } from "react";

import ContentEditor from "../components/content/ContentEditor";
import PublishBar from "../components/PublishBar";
import type { TagOut } from "../components/tags/TagPicker";

export default function QuestEditor() {
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [tags, setTags] = useState<TagOut[]>([]);
  const [cover, setCover] = useState<string | null>(null);
  const [body, setBody] = useState("");

  return (
    <ContentEditor
      title="Quest Editor"
      status="draft"
      version={1}
      actions={<PublishBar />}
      general={{
        title,
        slug,
        tags,
        cover,
        onTitleChange: setTitle,
        onSlugChange: setSlug,
        onTagsChange: setTags,
        onCoverChange: setCover,
      }}
      renderContent={() => (
        <textarea
          className="w-full h-40 border rounded p-2"
          placeholder="Quest content..."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      )}
    />
  );
}
