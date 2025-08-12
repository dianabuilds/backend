import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      // basename="/admin" добавится автоматически
      navigate("/");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Ошибка авторизации";
      setError(msg);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <form onSubmit={handleSubmit} className="w-full max-w-sm p-6 space-y-4 bg-white rounded shadow dark:bg-gray-800">
        <h1 className="text-xl font-bold text-center text-gray-800 dark:text-gray-100">Admin Login</h1>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Username</label>
          <input
            className="mt-1 w-full rounded border px-3 py-2 text-gray-900 dark:text-gray-100 dark:bg-gray-900"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">Password</label>
          <input
            type="password"
            className="mt-1 w-full rounded border px-3 py-2 text-gray-900 dark:text-gray-100 dark:bg-gray-900"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button
          type="submit"
          className="w-full rounded bg-gray-800 px-4 py-2 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          Войти
        </button>
      </form>
    </div>
  );
}

