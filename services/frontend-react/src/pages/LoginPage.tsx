import { useState } from "react";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const { login, loading, error } = useAuth();

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    login(username, password);
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <form
        onSubmit={handleSubmit}
        className="bg-panel border border-border rounded-xl p-8 w-full max-w-sm"
      >
        <h1 className="text-2xl font-bold text-accent mb-1">Meridian</h1>
        <p className="text-sm text-gray-400 mb-6">
          AI Investment Research Desk
        </p>

        <label className="block text-sm mb-1 text-gray-300">Username</label>
        <input
          className="w-full mb-4 px-3 py-2 rounded-lg bg-bg border border-border focus:border-accent outline-none"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="analyst"
          autoFocus
        />

        <label className="block text-sm mb-1 text-gray-300">Password</label>
        <input
          type="password"
          className="w-full mb-4 px-3 py-2 rounded-lg bg-bg border border-border focus:border-accent outline-none"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
        />

        {error && (
          <div className="mb-4 text-sm text-danger bg-danger/10 border border-danger/30 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-accent text-bg font-semibold py-2 rounded-lg disabled:opacity-50"
        >
          {loading ? "Signing in..." : "Sign in"}
        </button>

        <p className="text-xs text-gray-500 mt-4">
          Demo credentials: analyst / meridian123
        </p>
      </form>
    </div>
  );
}
