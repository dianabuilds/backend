import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { sendRUM } from "../perf/rum";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return; // защита от дабл-кликов
    setError(null);
    setLoading(true);
    const t0 = performance.now();
    try {
      await login(username, password);
      const dur = performance.now() - t0;
      sendRUM("login_attempt", { ok: true, dur_ms: Math.round(dur) });
      // basename="/admin" добавится автоматически
      navigate("/");
    } catch (err) {
      const dur = performance.now() - t0;
      const msg = err instanceof Error ? err.message : "Ошибка авторизации";
      sendRUM("login_attempt", {
        ok: false,
        dur_ms: Math.round(dur),
        error: String(msg).slice(0, 200),
      });
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm p-6 space-y-4 bg-white rounded shadow dark:bg-gray-800"
      >
        <h1 className="text-xl font-bold text-center text-gray-800 dark:text-gray-100">
          Admin Login
        </h1>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
            Username
          </label>
          <input
            className="mt-1 w-full rounded border px-3 py-2 text-gray-900 dark:text-gray-100 dark:bg-gray-900"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            disabled={loading}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
            Password
          </label>
          <input
            type="password"
            className="mt-1 w-full rounded border px-3 py-2 text-gray-900 dark:text-gray-100 dark:bg-gray-900"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded bg-gray-800 px-4 py-2 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Входим..." : "Войти"}
        </button>
      </form>
    </div>
  );
}
