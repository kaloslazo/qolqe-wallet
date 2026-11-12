#!/usr/bin/env bash
# Prueba de contrato con Schemathesis contra la app levantada en $QOLQE_URL (por defecto http://localhost:8000).
# Usa un usuario de carga para no tocar a los usuarios de los escenarios y excluye el cierre de cuenta.
#
# Dos pasadas:
#   gate       la API cumple lo que declara su OpenAPI: sin 500, códigos, tipos, esquema y cabeceras de
#              respuesta como dice el contrato, y ninguna ruta protegida responde sin token. Si falla, el
#              script sale con error y el pipeline no sigue.
#   hallazgos  reglas que el OpenAPI no declara (datos válidos rechazados por reglas de negocio, datos
#              inválidos aceptados, cabecera Allow en los 405). Ya están analizados en docs/informe.md:
#              se reportan, pero no bloquean.
set -euo pipefail
URL="${QOLQE_URL:-http://localhost:8000}"
SALIDA=reportes/schemathesis
CONOCIDOS=positive_data_acceptance,negative_data_rejection,unsupported_method,allow_header_conformance

preparar() {
  curl -sf -X DELETE "$URL/api/pruebas/reloj" > /dev/null
  curl -sf -X POST "$URL/api/pruebas/reiniciar" > /dev/null
  TOKEN=$(curl -sf -X POST "$URL/api/auth/login" -H 'Content-Type: application/json' \
    -d '{"celular":"900000001","pin":"2580"}' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
}

contrato() {
  local pasada=$1; shift
  st run "$URL/openapi.json" \
    -H "Authorization: Bearer $TOKEN" \
    --max-examples 20 \
    --include-path-regex '^/api/(limites|cuentas|transferencias|auth/login|usuarios)' \
    --exclude-path '/api/cuentas/me/cierre' \
    --report junit,html --report-dir "$SALIDA/$pasada" "$@"
}

mkdir -p "$SALIDA"

echo "== gate: la API cumple su contrato"
preparar
gate=0
contrato gate --checks all --exclude-checks "$CONOCIDOS" || gate=$?

echo "== hallazgos conocidos (no bloquean)"
preparar
contrato hallazgos --checks "$CONOCIDOS" || echo "hallazgos conocidos: ver $SALIDA/hallazgos y docs/informe.md"

exit "$gate"
