import { Outlet } from "react-router-dom";

export default function BlankLayout() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Outlet />
    </div>
  );
}
