"""
Thin wrapper around Bedrock's Claude models via the Converse API —
Bedrock's unified interface across model families, so switching models
later (Haiku -> Sonnet) doesn't require rewriting call sites.
"""
import logging

import boto3

logger = logging.getLogger(__name__)

NOVA_LITE_MODEL_ID = "us.amazon.nova-2-lite-v1:0"


class ClaudeClient:
    def __init__(self, model_id: str = NOVA_LITE_MODEL_ID, region_name: str = "us-east-1") -> None:
        self.model_id = model_id
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def generate(self, system_prompt: str, user_message: str, max_tokens: int = 1000) -> str:
        """Sends a single-turn request and returns the model's text response."""
        response = self.client.converse(
            modelId=self.model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_message}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0.3},
        )
        return response["output"]["message"]["content"][0]["text"]