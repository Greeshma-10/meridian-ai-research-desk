export interface ParsedVerdict {
  verdict: "Bullish" | "Bearish" | "Neutral" | "Unknown";
  confidence: "Low" | "Medium" | "High" | "Unknown";
  reasoning: string;
}

export function parseVerdict(rawText: string): ParsedVerdict {
  const verdictMatch = rawText.match(/VERDICT:\s*(Bullish|Bearish|Neutral)/i);
  const confidenceMatch = rawText.match(/CONFIDENCE:\s*(Low|Medium|High)/i);
  const reasoningMatch = rawText.match(/REASONING:\s*([\s\S]*)/i);

  const normalize = (s: string | undefined, fallback: string) =>
    s ? s.charAt(0).toUpperCase() + s.slice(1).toLowerCase() : fallback;

  return {
    verdict: (normalize(verdictMatch?.[1], "Unknown")) as ParsedVerdict["verdict"],
    confidence: (normalize(confidenceMatch?.[1], "Unknown")) as ParsedVerdict["confidence"],
    // Fall back to the raw text if parsing fails, so nothing is ever silently hidden
    reasoning: reasoningMatch?.[1]?.trim() || rawText,
  };
}
