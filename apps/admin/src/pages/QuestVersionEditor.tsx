import { Navigate, useParams } from "react-router-dom";

export default function QuestVersionEditor() {
  const { id } = useParams<{ id: string }>();
  return <Navigate to={`/nodes/${id ?? ""}`} replace />;
}

