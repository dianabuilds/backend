import { Card, CardContent } from "../components/ui/card";

export default function Dashboard() {
  return (
    <div className="space-y-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2 text-sm">
          <span className="rounded bg-green-100 px-2 py-1 text-green-800 dark:bg-green-900 dark:text-green-100">
            System OK
          </span>
          <span className="rounded bg-blue-100 px-2 py-1 text-blue-800 dark:bg-blue-900 dark:text-blue-100">
            Global
          </span>
          <span className="rounded bg-gray-100 px-2 py-1 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
            active
          </span>
        </div>
      </header>

      <div className="grid gap-4 md:grid-cols-5">
        {Array.from({ length: 5 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="h-24" />
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardContent className="h-64" />
        </Card>
        <Card>
          <CardContent className="h-64" />
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="h-32" />
          </Card>
        ))}
      </div>
    </div>
  );
}

