import { useQuery } from "@tanstack/react-query";
import type { TagOut as TagOutBase } from "../../openapi";
import { api } from "../../api/client";
import MultiSelectBase from "../ui/MultiSelectBase";

export type TagOut = TagOutBase & { id: string };

interface TagPickerProps {
  value: TagOut[];
  onChange: (val: TagOut[]) => void;
}

export default function TagPicker({ value, onChange }: TagPickerProps) {
  const { data: tags = [] } = useQuery<TagOut[]>({
    queryKey: ["admin-tags"],
    queryFn: async () => {
      const res = await api.get<TagOut[]>("/admin/tags");
      return res.data ?? [];
    },
  });

  return (
    <MultiSelectBase<TagOut>
      items={tags}
      values={value}
      onChange={onChange}
      getKey={(t) => t.slug}
      getLabel={(t) => t.name}
    />
  );
}
