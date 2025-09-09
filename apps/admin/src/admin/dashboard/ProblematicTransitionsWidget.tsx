import { Card, CardContent } from '../../components/ui/card';

export default function ProblematicTransitionsWidget() {
  return (
    <Card>
      <CardContent className="p-4 sm:p-6 space-y-2">
        <h2 className="font-semibold">Problematic transitions</h2>
        <ul className="text-sm space-y-1">
          <li>Node #450 — CTR 0.2%</li>
          <li>Node #451 — cycle detected</li>
        </ul>
        <button className="mt-2 rounded bg-gray-200 px-3 py-1 text-sm">Open graph</button>
      </CardContent>
    </Card>
  );
}
