#!/bin/bash
set -e
cd /workspaces/meridian-ai-research-desk

docker compose -f infra/docker-compose.yml up -d
sleep 3

(cd services/retrieval-service && uvicorn app.main:app --host 0.0.0.0 --port 8001 > /tmp/retrieval.log 2>&1 &)
(cd services/ingestion-service && uvicorn app.main:app --host 0.0.0.0 --port 8002 > /tmp/ingestion.log 2>&1 &)
(cd services/agent-orchestrator && uvicorn app.main:app --host 0.0.0.0 --port 8003 > /tmp/orchestrator.log 2>&1 &)
(cd services/api-gateway && uvicorn app.main:app --host 0.0.0.0 --port 8080 > /tmp/gateway.log 2>&1 &)

sleep 5
echo "--- Health checks ---"
curl -s http://localhost:8000/api/v1/heartbeat && echo " ✅ Chroma"
curl -s http://localhost:8001/health && echo " ✅ retrieval-service"
curl -s http://localhost:8002/health && echo " ✅ ingestion-service"
curl -s http://localhost:8003/health && echo " ✅ agent-orchestrator"
curl -s http://localhost:8080/health && echo " ✅ api-gateway"
