import { useState } from "react";
import ContentEditor from "../components/content/ContentEditor";
import MediaPicker from "../components/MediaPicker";
import TagSelect from "../components/TagSelect";
import PublishBar from "../components/PublishBar";

const TABS = ["General", "Content", "Relations", "AI", "Validation", "History", "Publishing", "Notifications"];

export default function CharacterEditor() {
  const [name, setName] = useState("");
  const [tags, setTags] = useState<string[]>([]);
  const [avatar, setAvatar] = useState<string | null>(null);
  const [body, setBody] = useState("");

  return (
    <ContentEditor
      title="Character Editor"
      tabs={TABS}
      actions={<PublishBar />}
      renderTab={(tab) => {
        switch (tab) {
          case "General":
            return (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium">Name</label>
                  <input
                    className="mt-1 border rounded px-2 py-1 w-full"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium">Tags</label>
                  <TagSelect value={tags} onChange={setTags} />
                </div>
                <div>
                  <label className="block text-sm font-medium">Avatar</label>
                  <MediaPicker value={avatar} onChange={setAvatar} height={120} />
                </div>
              </div>
            );
          case "Content":
            return (
              <textarea
                className="w-full h-40 border rounded p-2"
                placeholder="Character description..."
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
