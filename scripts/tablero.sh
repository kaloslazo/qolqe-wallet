#!/usr/bin/env bash
# Tablero de calidad con antes y después (reportes/tablero/tablero.html).
#   «antes»   calidad/antes.json: la entrega anterior (tag parte-3), medida con sus propios resultados y congelada en el repo.
#             Para rehacerlo con otra referencia:  scripts/tablero.sh --antes <tag|commit>   (solo cuenta lo estático:
#             escenarios, criterios, defectos; los resultados de las suites los pone quien tenga la corrida de ese árbol)
#   «después» el árbol actual, con reportes/resultados-api.json y reportes/selenium/junit.xml si existen
#             (corre antes  npm test  y  scripts/selenium.sh todo ).
# Uso, desde la raíz:  scripts/tablero.sh [--antes <referencia>]
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-.venv/bin/python}"
[ -x "$PY" ] || PY=.venv/Scripts/python   # Git Bash en Windows
if [ "${1:-}" = "--antes" ]; then
  REF="${2:?falta la referencia (tag o commit)}"
  TMP="$(mktemp -d)"
  git archive "$REF" | tar -x -C "$TMP"
  "$PY" .github/scripts/tablero.py instantanea --repo "$TMP" --nombre "Entrega anterior ($REF)" --salida calidad/antes.json
fi
[ -f calidad/antes.json ] || { echo "falta calidad/antes.json: corre  scripts/tablero.sh --antes <tag>"; exit 1; }
ARGS=(--repo . --nombre "Entrega final" --salida calidad/despues.json)
[ -f reportes/resultados-api.json ] && ARGS+=(--api-json reportes/resultados-api.json)
[ -f reportes/selenium/junit.xml ] && ARGS+=(--web-junit reportes/selenium/junit.xml)
"$PY" .github/scripts/tablero.py instantanea "${ARGS[@]}"
ENL=()
[ -f reportes/diagnostico/diagnostico.html ] && ENL+=(--enlace "Diagnóstico por prueba=../diagnostico/diagnostico.html")
"$PY" .github/scripts/tablero.py tablero --antes calidad/antes.json --despues calidad/despues.json \
  --salida reportes/tablero/tablero.html "${ENL[@]}"
echo "Abrir reportes/tablero/tablero.html"
