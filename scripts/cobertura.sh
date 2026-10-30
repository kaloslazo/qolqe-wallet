#!/usr/bin/env bash
# Cobertura de la API en local: corre los escenarios y Schemathesis contra la misma app y compara lo que cada uno
# provocó según el log de la app. Escribe docs/cobertura-contrato.md (el pipeline publica lo mismo en Pages).
set -euo pipefail
cd "$(dirname "$0")/.."

URL=http://localhost:8000
R=reportes/cobertura
mkdir -p "$R"

if curl -sf "$URL/api/salud" > /dev/null; then
  echo "Ya hay una app en el puerto 8000: ciérrala para que el log sea solo de esta corrida."; exit 1
fi
.venv/bin/python -m uvicorn qolqe.main:app --port 8000 > "$R/log-app.txt" 2>&1 &
APP=$!
trap 'kill $APP 2> /dev/null' EXIT
for _ in $(seq 1 60); do curl -sf "$URL/api/salud" > /dev/null && break; sleep 1; done
curl -sf "$URL/openapi.json" -o "$R/openapi.json"

# los fallos esperados (@fail) y los hallazgos de Schemathesis no deben cortar el script
QOLQE_URL=$URL npm test || true
cp "$R/log-app.txt" "$R/log-api.txt"
desde=$(wc -l < "$R/log-app.txt")
PATH="$PWD/.venv/bin:$PATH" QOLQE_URL=$URL bash scripts/contrato.sh || true
tail -n +"$((desde + 1))" "$R/log-app.txt" > "$R/log-contrato.txt"

.venv/bin/python .github/scripts/cobertura_contrato.py --openapi "$R/openapi.json" \
  --log-api "$R/log-api.txt" --log-contrato "$R/log-contrato.txt" \
  --junit-contrato "$(ls -t reportes/schemathesis/junit-*.xml | head -1)" \
  --md docs/cobertura-contrato.md
