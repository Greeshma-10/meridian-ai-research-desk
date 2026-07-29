import { useState } from "react";
import type { AnalysisResult, CitationReport } from "../types";
import VerdictCard from "./VerdictCard";

const PREVIEW_LENGTH = 220;

function TrustBadge({ report }: { report: CitationReport }) {
  const pct = Math.round(report.trust_score * 100);
  const color =
    pct >= 80 ? "text-accent border-accent/40 bg-accent/10"
    : pct >= 50 ? "text-warn border-warn/40 bg-warn/10"
    : "text-danger border-danger/40 bg-danger/10";

  return (
    <span className={`text-xs px-2 py-1 rounded-full border ${color} whitespace-nowrap`}>
      Trust {pct}%
      {report.fabricated_count > 0 && ` · ${report.fabricated_count} fabricated`}
    </span>
  );
}

function Section({
  title,
  icon,
  text,
  colorClass,
  citationReport,
  defaultOpen = false,
}: {
  title: string;
  icon: string;
  text: string;
  colorClass: string;
  citationReport: CitationReport;
  defaultOpen?: boolean;
}) {
  const [expanded, setExpanded] = useState(defaultOpen);
  const isLong = text.length > PREVIEW_LENGTH;
  const displayText = expanded || !isLong ? text : text.slice(0, PREVIEW_LENGTH).trimEnd() + "...";

  return (
    <div className={`bg-panel border-l-4 ${colorClass} rounded-xl p-5 mb-4`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between mb-2 text-left"
      >
        <h2 className="font-semibold uppercase text-sm tracking-wide">
          {icon} {title}
        </h2>
        <div className="flex items-center gap-2">
          <TrustBadge report={citationReport} />
          <span className="text-gray-500 text-xs">
            {expanded ? "▲ Collapse" : "▼ Expand"}
          </span>
        </div>
      </button>

      <p className="text-sm text-gray-300 whitespace-pre-wrap leading-relaxed">
        {displayText}
      </p>

      {isLong && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-xs text-accent hover:underline mt-2"
        >
          {expanded ? "Show less" : "Read full analysis"}
        </button>
      )}
    </div>
  );
}

export default function ResultsDisplay({ result }: { result: AnalysisResult }) {
  return (
    <div>
      <VerdictCard
        rawText={result.final_verdict}
        citationReport={result.citation_verification.portfolio_manager}
      />
      <Section
        title="Bull Thesis"
        icon="🐂"
        text={result.bull_thesis}
        colorClass="border-accent"
        citationReport={result.citation_verification.bull}
      />
      <Section
        title="Bear Thesis"
        icon="🐻"
        text={result.bear_thesis}
        colorClass="border-danger"
        citationReport={result.citation_verification.bear}
      />
      <Section
        title="Risk Assessment"
        icon="⚠️"
        text={result.risk_assessment}
        colorClass="border-warn"
        citationReport={result.citation_verification.risk}
      />
    </div>
  );
}
