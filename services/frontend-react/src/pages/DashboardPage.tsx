import { useState, useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { analyze } from "../api/client";
import AnalysisForm from "../components/AnalysisForm";
import ResultsDisplay from "../components/ResultsDisplay";
import HistoryPanel from "../components/HistoryPanel";
import type { AnalysisResult, HistoryEntry } from "../types";

const HISTORY_KEY = "meridian_history";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem(HISTORY_KEY);
    if (stored) setHistory(JSON.parse(stored));
  }, []);

  function saveToHistory(entry: AnalysisResult) {
    const newEntry: HistoryEntry = {
      ...entry,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
    };
    const updated = [newEntry, ...history].slice(0, 20); // cap at 20 to avoid unbounded growth
    setHistory(updated);
    localStorage.setItem(HISTORY_KEY, JSON.stringify(updated));
  }

  async function handleSubmit(ticker: string, query: string) {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await analyze(ticker, query);
      setResult(data);
      saveToHistory(data);
    } catch (err: any) {
      if (err.code === "ECONNABORTED") {
        setError("Request timed out — the agent pipeline can take up to 3 minutes for a new ticker.");
      } else {
        setError(err.response?.data?.detail || "Something went wrong running this analysis.");
      }
    } finally {
      setLoading(false);
    }
  }

  function clearHistory() {
    setHistory([]);
    localStorage.removeItem(HISTORY_KEY);
  }

  return (
    <div className="min-h-screen bg-bg text-gray-100 p-4 sm:p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-accent">📊 Meridian</h1>
          <p className="text-sm text-gray-400">
            Signed in as {user?.username} ({user?.role})
          </p>
        </div>
        <button
          onClick={logout}
          className="text-sm text-gray-400 hover:text-danger border border-border rounded-lg px-3 py-1.5"
        >
          Sign out
        </button>
      </div>

      <AnalysisForm onSubmit={handleSubmit} loading={loading} />

      {error && (
        <div className="mb-6 text-sm text-danger bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {loading && (
        <div className="mb-6 text-sm text-gray-400 bg-panel border border-border rounded-lg px-4 py-3 animate-pulse">
          Running Research → Bull → Bear → Risk → Portfolio Manager... this takes 20-40s for a cached ticker, longer for a new one.
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          {result && <ResultsDisplay result={result} />}
        </div>
        <div>
          <HistoryPanel
            history={history}
            onSelect={(entry) => setResult(entry)}
            onClear={clearHistory}
          />
        </div>
      </div>
    </div>
  );
}
