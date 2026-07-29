import type { HistoryEntry } from "../types";

interface Props {
  history: HistoryEntry[];
  onSelect: (entry: HistoryEntry) => void;
  onClear: () => void;
}

export default function HistoryPanel({ history, onSelect, onClear }: Props) {
  if (history.length === 0) {
    return (
      <div className="text-sm text-gray-500 bg-panel border border-border rounded-xl p-4">
        No past analyses yet — run one above to see it appear here.
      </div>
    );
  }

  return (
    <div className="bg-panel border border-border rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-300">Recent Analyses</h3>
        <button onClick={onClear} className="text-xs text-gray-500 hover:text-danger">
          Clear
        </button>
      </div>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {history.map((entry) => (
          <button
            key={entry.id}
            onClick={() => onSelect(entry)}
            className="w-full text-left px-3 py-2 rounded-lg bg-bg border border-border hover:border-accent transition-colors"
          >
            <div className="flex justify-between items-center">
              <span className="font-medium text-accent">{entry.ticker}</span>
              <span className="text-xs text-gray-500">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-xs text-gray-400 truncate">{entry.query}</p>
          </button>
        ))}
      </div>
    </div>
  );
}
