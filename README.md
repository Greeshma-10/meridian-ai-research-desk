# Meridian — Multi-Agent AI Investment Research Platform

Meridian is an AI-powered research desk that answers investment questions about publicly traded companies by retrieving real SEC filings, then running a structured, adversarial debate between four AI agents — Bull, Bear, Risk Manager, and Portfolio Manager — before returning a cited, verified verdict.

Built from scratch as an end-to-end learning project covering RAG, multi-agent orchestration, microservice architecture, MLOps, CI/CD, and cloud infrastructure on AWS.

> **Disclaimer:** This is a research/learning project, not a financial product. Nothing it produces is investment advice.

---

## What it actually does

Ask a question like *"Should I be worried about Apple's competitive position?"* and Meridian:

1. Fetches the company's real 10-K filing from SEC EDGAR (if not already cached)
2. Breaks it into meaningfully-sized, section-aware chunks
3. Retrieves the most relevant excerpts using hybrid search (semantic + keyword) and reranking
4. Runs four AI agents in sequence: a **Bull** builds the strongest optimistic case, a **Bear** directly attacks the Bull's specific claims, a **Risk Manager** independently flags concrete dangers, and a **Portfolio Manager** weighs all three into a final verdict
5. Verifies every citation the agents made against the real source text, catching fabricated or unsupported claims before returning the answer

---

## Architecture

```
Browser
   │
   ▼
api-gateway  (public entrypoint, routing + CORS)
   │
   ▼
agent-orchestrator  (LangGraph state machine)
   │
   ├──► ingestion-service ──► SEC EDGAR (fetch, parse, chunk, embed)
   │
   └──► retrieval-service ──► Chroma (hybrid search: vector + BM25 + rerank)
            │
            ▼
   Research → Bull → Bear → Risk → Portfolio Manager → Citation Verification
   (all four agent LLM calls via Amazon Bedrock / Nova)
```

Each box above is an independently deployable microservice, containerized with Docker, communicating over HTTP — not shared code imports. Retrieval and ingestion each own their own responsibility; the orchestrator coordinates but doesn't know how retrieval works internally, and vice versa.

---

## Tech stack, and why each piece is there

| Tool | Role in the pipeline |
|---|---|
| **FastAPI** | Every microservice's HTTP interface — lightweight, async, auto-validates request/response shapes via Pydantic |
| **SEC EDGAR API** | Source of real, free, public company filings (10-Ks) |
| **BeautifulSoup + lxml** | Strips SEC's messy iXBRL/HTML filings down to clean readable text |
| **LangChain text splitters + tiktoken** | Section-aware chunking, sized in actual tokens (not characters), so chunks match what the embedding model sees |
| **Amazon Titan Embeddings** (Bedrock) | Converts text chunks into vectors for semantic search |
| **Chroma** | Vector database storing chunk embeddings, queryable by meaning and filterable by ticker |
| **BM25 (rank-bm25)** | Classic keyword search, run alongside vector search — catches literal-term matches that pure semantic search can miss |
| **Reciprocal Rank Fusion** | Merges vector + BM25 result rankings fairly, without needing to compare incompatible raw scores |
| **Cross-encoder reranker** (sentence-transformers) | Re-scores the fused candidates by jointly evaluating query + chunk together — more accurate than embedding similarity alone |
| **LangGraph** | Defines the multi-agent workflow as an explicit state machine (Research → Bull → Bear → Risk → PM → Verify) |
| **Amazon Nova** (Bedrock) | The LLM powering all four agent personalities |
| **Custom citation verifier** | Pure Python, zero-cost check that every `[chunk_id]` an agent cites is real and reasonably supported by its source text |
| **Docker / Docker Compose** | Containerizes every service; Compose runs Chroma locally |
| **GitHub Actions (CI)** | Runs unit + integration tests and builds all Docker images on every push |
| **Terraform** | Defines and provisions real AWS infrastructure (VPC, ECS/Fargate, Cloud Map, EFS, ALB, ECR) as code |
| **AWS ECS/Fargate** | Runs the containerized services in the cloud, no server management |
| **AWS Cloud Map** | Service discovery — lets containers find each other by DNS name instead of hardcoded addresses |
| **pytest** | Unit tests (pure logic, e.g. chunking/section-splitting) and integration tests (real services, real HTTP calls) |

---

## Project structure

```
meridian-ai-research-desk/
├── services/
│   ├── ingestion-service/      # EDGAR fetch → parse → chunk → embed → store
│   ├── retrieval-service/      # Hybrid search + reranking
│   ├── agent-orchestrator/     # LangGraph multi-agent pipeline
│   ├── api-gateway/            # Public entrypoint
│   └── frontend/               # Simple HTML/JS demo UI
├── infra/
│   ├── terraform/              # AWS infrastructure as code
│   └── docker-compose.yml      # Local Chroma
├── tests/
│   └── integration/            # Cross-service tests against real running services
├── .github/workflows/ci.yml    # CI pipeline
└── scripts/start_all.sh        # Convenience script to start all local services
```

---

## Running it locally

Requires Docker, Python 3.12, and AWS credentials with Bedrock access configured as environment variables.

```bash
# Start Chroma + all 4 services
bash scripts/start_all.sh

# Verify everything's healthy
curl http://localhost:8080/health

# Run a real analysis
curl -X POST http://localhost:8080/analyze \
  -H "Content-Type: application/json" \
  -d '{"ticker": "AAPL", "query": "What is Apples biggest competitive risk?"}'
```

## Deploying to AWS

```bash
cd infra/terraform
terraform init
terraform plan -out=tfplan
terraform apply tfplan

# Get the public URL
terraform output load_balancer_url

# Tear down when done (Fargate bills per minute)
terraform destroy
```

---

## Design decisions worth knowing about

- **Adversarial agent sequencing is deliberate.** Bear sees Bull's output and is instructed to directly attack it, rather than both agents running blind and simultaneously — this counters LLMs' tendency toward sycophantic agreement and produces sharper, more useful disagreement.
- **Citation verification is local and free**, not another LLM call — it catches fabricated citations with certainty (string matching against real retrieved chunks) and flags weakly-supported claims approximately (word-overlap scoring), rather than spending money to verify every claim semantically.
- **No NAT Gateway in the AWS deployment** — services run in public subnets behind security groups instead, a conscious cost trade-off (NAT Gateways bill ~$32/month idle) appropriate for a personal-budget demo, not a production security posture.
- **IAM permissions are intentionally broad** during this build phase (documented training-wheels approach), not least-privilege — a known, flagged simplification rather than an oversight.
- **Retrieval is its own microservice, not a shared library**, specifically because it's core business logic with its own lifecycle — a lesson learned firsthand after an earlier attempt to share Python code directly between services created fragile, duplicated state.

---

## Beyond the core pipeline

The following were added after the initial build, each using free-tier or self-hosted tools rather than paid cloud services:

| Capability | How it's built |
|---|---|
| **Knowledge graph** | Neo4j AuraDB (free tier). Entities and relationships (competitors, risk categories) are extracted from risk-factor chunks via Nova, then stored as a graph — enabling multi-hop queries pure vector search can't answer, e.g. "what risk categories do Apple and Microsoft have in common?" |
| **Citation verification** | Local, zero-cost check run after every agent debate: confirms every `[chunk_id]` an agent cites genuinely exists in the retrieved context (catching fabrication with certainty) and flags weakly-supported claims via word-overlap scoring (an approximate, honestly-limited heuristic — noted in code comments) |
| **Authentication & RBAC** | JWT-based login on api-gateway, with `user`/`admin` roles. Protects `/analyze` from unauthenticated use, which also protects against unbounded Bedrock spend from an open endpoint |
| **Monitoring** | Prometheus (self-hosted, Docker) scrapes api-gateway's instrumented `/metrics` endpoint; Grafana dashboards visualize request rate and latency in real time |
| **Least-privilege IAM** | The original broad `MeridianProjectFullAccess` policy (used deliberately as training wheels through the build) was replaced with a policy scoped to the actual, audited set of AWS actions the project uses — verified via a clean `terraform plan` against the narrowed permissions |
| **Fine-tuning (LoRA)** | A local, CPU-only LoRA fine-tune of DistilBERT for risk-category classification (`experiments/lora-finetuning/`) — trains ~1.1% of the model's parameters, demonstrating the core mechanics and cost trade-off versus using an LLM API call for the same narrow task. Bedrock's native fine-tuning was evaluated and intentionally skipped, since serving a fine-tuned model there requires Provisioned Throughput — a per-hour cost with no meaningful free tier, not justified for this project's scope |

## What's genuinely still open

No end-to-end automated eval suite for agent output quality (beyond citation verification), no OpenTelemetry distributed tracing across services, and the frontend is a functional but minimal demo UI rather than a polished production interface.