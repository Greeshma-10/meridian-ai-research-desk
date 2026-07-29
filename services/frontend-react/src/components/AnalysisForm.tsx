import { useState } from "react";

interface Props {
  onSubmit: (ticker: string, query: string) => void;
  loading: boolean;
}

export default function AnalysisForm({ onSubmit, loading }: Props) {
  const [ticker, setTicker] = useState("AAPL");
  const [query, setQuery] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ticker.trim() || !query.trim()) return;
    onSubmit(ticker.trim().toUpperCase(), query.trim());
  }

  return (
    <form onSubmit={handleSubmit} className="bg-panel border border-border rounded-xl p-5 mb-6">
      <div className="flex flex-col sm:flex-row gap-3">
        <input
          className="sm:w-32 px-3 py-2 rounded-lg bg-bg border border-border focus:border-accent outline-none"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          placeholder="Ticker"
        />
        <input
          className="flex-1 px-3 py-2 rounded-lg bg-bg border border-border focus:border-accent outline-none"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a research question, e.g. 'Should I be worried about competition?'"
        />
        <button
          type="submit"
          disabled={loading}
          className="bg-accent text-bg font-semibold px-6 py-2 rounded-lg disabled:opacity-50 whitespace-nowrap"
        >
          {loading ? "Analyzing..." : "Run Analysis"}
        </button>
      </div>
    </form>
  );
}
