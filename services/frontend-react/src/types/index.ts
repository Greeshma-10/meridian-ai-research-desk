export interface CitationReport {
  total_citations: number;
  fabricated_count: number;
  low_support_count: number;
  trust_score: number;
}

export interface AnalysisResult {
  ticker: string;
  query: string;
  bull_thesis: string;
  bear_thesis: string;
  risk_assessment: string;
  final_verdict: string;
  citation_verification: {
    bull: CitationReport;
    bear: CitationReport;
    risk: CitationReport;
    portfolio_manager: CitationReport;
  };
}

export interface HistoryEntry extends AnalysisResult {
  id: string;
  timestamp: number;
}

export interface User {
  username: string;
  role: "user" | "admin";
}
