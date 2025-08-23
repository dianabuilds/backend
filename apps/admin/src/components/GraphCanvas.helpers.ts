export type GraphNode = {
  key: string;
  title: string;
  type?: "start" | "normal" | "end";
};

export type GraphEdge = {
  from_node_key: string;
  to_node_key: string;
  label?: string | null;
};

export interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeDoubleClick?: (nodeKey: string) => void;
  onCreateEdge?: (fromKey: string, toKey: string) => void;
  height?: number; // px
}
