#!/usr/bin/env bash
# Corre las pruebas de API contra una app con su log guardado y arma el diagnóstico por prueba
# (reportes/diagnostico/diagnostico.html): cada prueba que no pasó limpia, con los requests que hizo y la traza del servidor.
# Es lo mismo que hace el job «reportes» del pipeline. Uso, desde la raíz y con el .venv activo:  scripts/diagnostico.sh
set -uo pipefail
PUERTO="${QOLQE_PUERTO:-8000}"
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=.venv/Scripts/python   # Git Bash en Windows
mkdir -p reportes
QOLQE_MODO_PRUEBA=1 "$PY" -m uvicorn qolqe.main:app --port "$PUERTO" > reportes/log-api.txt 2>&1 &
APP=$!
trap 'kill $APP 2>/dev/null' EXIT
for _ in $(seq 1 60); do curl -sf "http://localhost:$PUERTO/api/salud" > /dev/null && break; sleep 1; done
npx bddgen && QOLQE_URL="http://localhost:$PUERTO" npx playwright test
"$PY" .github/scripts/diagnostico.py --playwright reportes/resultados-api.json --log-api reportes/log-api.txt \
  --salida reportes/diagnostico
echo "Abrir reportes/diagnostico/diagnostico.html"
