import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

interface DashboardData {
  drafts: number;
  reviews: number;
  published: number;
}

export default function ContentDashboard() {
  const { data } = useQuery({
    queryKey: ["content", "dashboard"],
    queryFn: async () => {
      const res = await api.get<DashboardData>("/admin/content");
      return res.data;
    },
  });

  return (
    <div className="space-y-2">
      <h1 className="text-xl font-semibold mb-4">Content Dashboard</h1>
      <div>Drafts: {data?.drafts ?? 0}</div>
      <div>Reviews: {data?.reviews ?? 0}</div>
      <div>Published: {data?.published ?? 0}</div>
    </div>
  );
}
