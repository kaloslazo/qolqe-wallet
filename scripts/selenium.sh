#!/usr/bin/env bash
# Pruebas E2E con Selenium + pytest-bdd.
# Uso: scripts/selenium.sh [preparar | todo | demo | defectos | navegadores | movil | grid | grid-parar | romper | ia | reporte] [args de pytest]
set -euo pipefail
cd "$(dirname "$0")/.."

PY=.venv/bin/python
REPORTES=reportes/selenium
GRID=http://localhost:4444
mkdir -p "$REPORTES"

pytest_e2e() {
  "$PY" -m pytest tests/e2e -p no:cacheprovider "$@"
}

modo="${1:-todo}"
shift || true

case "$modo" in
  # antes de exponer: levanta el Grid en Docker y calienta drivers y navegadores con una corrida rápida
  preparar)
    docker compose -f docker-compose.grid.yml up -d
    for _ in $(seq 1 60); do curl -sf "$GRID/status" | grep -q '"ready": *true' && break; sleep 2; done
    pytest_e2e --headless -m happy -q --reporte-bdd reporte-bdd-preparar.html "$@"
    echo "Listo. Grid: $GRID/ui · navegador de Docker en vivo: http://localhost:7900 (Chromium) y :7901 (Firefox)" ;;

  # los 15 escenarios + los 3 defectos conocidos (fallos esperados) en Chrome sin ventana, con reporte HTML
  todo)
    pytest_e2e --headless --html="$REPORTES/reporte.html" --self-contained-html "$@" ;;

  # flujo feliz con Chrome visible, resaltando cada elemento antes de usarlo
  demo)
    pytest_e2e -m happy --demo --reporte-bdd reporte-bdd-demo.html "$@" ;;

  # los defectos conocidos como fallas reales (rojo), con Chrome visible: así se ve cuando algo se rompe
  defectos)
    pytest_e2e -m defecto --runxfail --demo --reporte-bdd reporte-bdd-defectos.html "$@" || true
    open "$REPORTES/reporte-bdd-defectos.html" 2>/dev/null || true ;;

  # la misma suite en cada navegador instalado (Selenium Manager descarga lo que falte)
  navegadores)
    for navegador in chrome edge firefox; do
      echo "== $navegador"
      pytest_e2e --headless --navegador "$navegador" -q --reporte-bdd "reporte-bdd-$navegador.html" "$@"
    done ;;

  # emulación de iPhone 12 Pro en Chrome
  movil)
    pytest_e2e --movil --demo -m happy --reporte-bdd reporte-bdd-movil.html "$@" ;;

  # Selenium Grid 4 en Docker: Chromium y Firefox remotos (consola en http://localhost:4444/ui;
  # el navegador del contenedor se ve en vivo en http://localhost:7900 y :7901)
  grid)
    docker compose -f docker-compose.grid.yml up -d
    for _ in $(seq 1 60); do curl -sf "$GRID/status" | grep -q '"ready": *true' && break; sleep 2; done
    for navegador in chrome firefox; do
      echo "== grid · $navegador"
      pytest_e2e --grid "$GRID" --navegador "$navegador" --url-navegador http://host.docker.internal:8000 -q \
        --reporte-bdd "reporte-bdd-grid-$navegador.html" "$@"
    done ;;

  grid-parar)
    docker compose -f docker-compose.grid.yml down ;;

  # IA: primero falla con un localizador roto, luego la IA lo repara (requiere GEMINI_API_KEY o ANTHROPIC_API_KEY)
  romper)
    pytest_e2e -m happy --romper --reporte-bdd reporte-bdd-romper.html "$@" || true ;;
  ia)
    pytest_e2e -m happy --romper --sanar --demo -s --reporte-bdd reporte-bdd-ia.html "$@"
    echo "Reparaciones registradas en $REPORTES/sanaciones.json" ;;

  reporte)
    open "$REPORTES/reporte-bdd.html" 2>/dev/null || xdg-open "$REPORTES/reporte-bdd.html" ;;

  *)
    sed -n '2,3p' "$0"; exit 1 ;;
esac
