#!/usr/bin/env bash
# Sube los resultados de la corrida a Qase (gestión de casos): una corrida de Qase por pipeline de main,
# con los JUnit de api, del gate del contrato y de la web. Lo llama el job reportes, y solo si existe el
# secreto QASE_TESTOPS_API_TOKEN (docs/gestion-casos.md).
# Uso: .github/scripts/qase.sh SITIO
set -euo pipefail
SITIO="${1:-sitio}"
VERSION=v0.7.0
QASECTL="${RUNNER_TEMP:-/tmp}/qasectl"
curl -sSfL -o "$QASECTL" "https://github.com/qase-tms/qasectl/releases/download/$VERSION/qasectl-linux-amd64"
chmod +x "$QASECTL"

q() { "$QASECTL" "$@" --project "$QASE_PROYECTO" --token "$QASE_TOKEN"; }

q testops run create --title "Pipeline #${GITHUB_RUN_NUMBER} · ${GITHUB_SHA::7}" \
  --description "${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}" --output qase.env
ID=$(cut -d= -f2 qase.env)
echo "corrida de Qase: $ID"

subir() {
  local suite=$1 archivo=$2
  [ -f "$archivo" ] || return 0
  q testops result upload --id "$ID" --format junit --path "$archivo" --suite "$suite"
}

subir "API" "$SITIO/api/junit-api.xml"
for f in "$SITIO"/contrato/gate/junit-*.xml; do subir "Contrato" "$f"; done
for nav in chrome firefox; do subir "Web $nav" "$SITIO/web-$nav/junit.xml"; done

# la corrida se cierra siempre: el plan gratis admite solo dos abiertas
q testops run complete --id "$ID"
