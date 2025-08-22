import { useState } from "react";
import ContentEditor from "../components/content/ContentEditor";
import MediaPicker from "../components/MediaPicker";
import TagSelect from "../components/TagSelect";
import PublishBar from "../components/PublishBar";

const TABS = ["General", "Content", "Relations", "AI", "Validation", "History", "Publishing", "Notifications"];

export default function QuestEditor() {
  const [title, setTitle] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [cover, setCover] = useState<string | null>(null);
  const [body, setBody] = useState("");

  return (
    <ContentEditor
      title="Quest Editor"
      tabs={TABS}
      actions={<PublishBar />}
      renderTab={(tab) => {
        switch (tab) {
          case "General":
            return (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium">Title</label>
                  <input
                    className="mt-1 border rounded px-2 py-1 w-full"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">Tags</label>
                  <TagSelect value={tags} onChange={setTags} />
                </div>
                <div>
                  <label className="block text-sm font-medium">Cover</label>
                  <MediaPicker value={cover} onChange={setCover} />
                </div>
              </div>
            );
          case "Content":
            return (
              <textarea
                className="w-full h-40 border rounded p-2"
                placeholder="Quest content..."
                value={body}
                onChange={(e) => setBody(e.target.value)}
              />
            );
          default:
            return <div className="text-sm text-gray-500">No content for {tab} yet.</div>;
        }
      }}
    />
  );
}
