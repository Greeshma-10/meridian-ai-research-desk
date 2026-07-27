"""
Generates embeddings for text using Amazon Bedrock's Titan Embeddings model.

Design note: this class only knows how to turn text into vectors — it
doesn't know about chunks, filings, or storage. Single Responsibility.
"""
import json
import logging

import boto3

logger = logging.getLogger(__name__)

TITAN_MODEL_ID = "amazon.titan-embed-text-v2:0"


class BedrockEmbedder:
    def __init__(self, region_name: str = "us-east-1") -> None:
        self.client = boto3.client("bedrock-runtime", region_name=region_name)

    def embed_text(self, text: str) -> list[float]:
        """Returns a vector embedding for a single piece of text."""
        body = json.dumps({"inputText": text})

        response = self.client.invoke_model(
            modelId=TITAN_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Embeds multiple texts. Titan doesn't support true batch requests,
        so we loop — but we log progress since this is where a large
        filing (100+ chunks) will visibly take some time.
        """
        embeddings = []
        for i, text in enumerate(texts):
            embeddings.append(self.embed_text(text))
            if (i + 1) % 20 == 0:
                logger.info(f"Embedded {i + 1}/{len(texts)} chunks")
        return embeddings