import { useState } from "react";
import { parseVerdict } from "../utils/parseVerdict";
import type { CitationReport } from "../types";

const VERDICT_STYLES: Record<string, { bg: string; border: string; text: string; icon: string }> = {
  Bullish: { bg: "bg-accent/10", border: "border-accent", text: "text-accent", icon: "📈" },
  Bearish: { bg: "bg-danger/10", border: "border-danger", text: "text-danger", icon: "📉" },
  Neutral: { bg: "bg-info/10", border: "border-info", text: "text-info", icon: "⚖️" },
  Unknown: { bg: "bg-gray-500/10", border: "border-gray-500", text: "text-gray-400", icon: "❓" },
};

const CONFIDENCE_WIDTH: Record<string, string> = {
  Low: "33%",
  Medium: "66%",
  High: "100%",
  Unknown: "0%",
};

function TrustBadge({ report }: { report: CitationReport }) {
  const pct = Math.round(report.trust_score * 100);
  const color =
    pct >= 80 ? "text-accent border-accent/40 bg-accent/10"
    : pct >= 50 ? "text-warn border-warn/40 bg-warn/10"
    : "text-danger border-danger/40 bg-danger/10";
  return (
    <span className={`text-xs px-2 py-1 rounded-full border ${color} whitespace-nowrap`}>
      Trust {pct}%
    </span>
  );
}

export default function VerdictCard({
  rawText,
  citationReport,
}: {
  rawText: string;
  citationReport: CitationReport;
}) {
  const { verdict, confidence, reasoning } = parseVerdict(rawText);
  const style = VERDICT_STYLES[verdict] ?? VERDICT_STYLES.Unknown;
  const [expanded, setExpanded] = useState(false);

  const PREVIEW_LENGTH = 260;
  const isLong = reasoning.length > PREVIEW_LENGTH;
  const displayReasoning =
    expanded || !isLong ? reasoning : reasoning.slice(0, PREVIEW_LENGTH).trimEnd() + "...";

  return (
    <div className={`rounded-2xl border-2 ${style.border} ${style.bg} p-6 mb-6`}>
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs uppercase tracking-widest text-gray-400 font-semibold">
          Portfolio Manager's Verdict
        </span>
        <TrustBadge report={citationReport} />
      </div>

      <div className="flex items-center gap-4 mb-5">
        <span className="text-5xl">{style.icon}</span>
        <div>
          <div className={`text-3xl font-bold ${style.text}`}>{verdict}</div>
          <div className="text-xs text-gray-400 mt-1">Final Recommendation</div>
        </div>
      </div>

      <div className="mb-5">
        <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
          <span>Confidence</span>
          <span className={style.text}>{confidence}</span>
        </div>
        <div className="w-full h-2 bg-black/30 rounded-full overflow-hidden">
          <div
            className={`h-full ${style.text.replace("text-", "bg-")} transition-all duration-500`}
            style={{ width: CONFIDENCE_WIDTH[confidence] ?? "0%" }}
          />
        </div>
      </div>

      <div className="border-t border-white/10 pt-4">
        <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
          {displayReasoning}
        </p>
        {isLong && (
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-accent hover:underline mt-2"
          >
            {expanded ? "Show less" : "Read full reasoning"}
          </button>
        )}
      </div>
    </div>
  );
}
