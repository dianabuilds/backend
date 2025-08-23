import { useState } from "react";
import ContentEditor from "../components/content/ContentEditor";
import PublishBar from "../components/PublishBar";

export default function CharacterEditor() {
  const [title, setTitle] = useState("");
  const [slug, setSlug] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [cover, setCover] = useState<string | null>(null);
  const [body, setBody] = useState("");

  return (
    <ContentEditor
      title="Character Editor"
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
          placeholder="Character description..."
          value={body}
          onChange={(e) => setBody(e.target.value)}
        />
      )}
    />
  );
}
