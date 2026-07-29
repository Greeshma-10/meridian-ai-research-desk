"""
Extracts named competitors and risk categories from a Risk Factors
chunk using Nova, returning structured JSON. Uses the same Bedrock
model already approved for the agent pipeline — no new setup.
"""
import json
import logging

import boto3

logger = logging.getLogger(__name__)

NOVA_MODEL_ID = "us.amazon.nova-2-lite-v1:0"

EXTRACTION_PROMPT = """Extract structured data from this SEC risk factor excerpt. \
Return ONLY valid JSON, no other text, in this exact format:
{"competitors": ["Company Name", ...], "risk_categories": ["category", ...]}

Risk categories should be short, general labels (e.g. "supply chain", "regulatory", \
"cybersecurity", "competition", "intellectual property") — not full sentences.
If no competitors are explicitly named, return an empty list. Do NOT include the \
filing company itself in the competitors list."""

class EntityExtractor:
    def __init__(self, region_name: str = "us-east-1") -> None:
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def extract(self, chunk_text: str) -> dict:
        response = self.client.converse(
            modelId=NOVA_MODEL_ID,
            system=[{"text": EXTRACTION_PROMPT}],
            messages=[{"role": "user", "content": [{"text": chunk_text[:2000]}]}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.0},
        )
        raw = response["output"]["message"]["content"][0]["text"]

        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse extraction output: {raw[:200]}")
            return {"competitors": [], "risk_categories": []}
