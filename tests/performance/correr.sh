#!/usr/bin/env bash
# corre una prueba de punta a punta y deja todo en resultados/<prueba>/
# uso: ./correr.sh <humo|demo|carga|pico|estres|resistencia> [usuarios]
cd "$(dirname "$0")"

prueba=${1:?indica la prueba: humo, demo, carga, pico, estres o resistencia}
usuarios=${2:-1000}
salida=resultados/$prueba
py=../../.venv/bin/python
rm -rf "$salida" && mkdir -p "$salida"

# qolqe recien levantado en docker, con 1 cpu y 1 gb
docker rm -f qolqe-perf > /dev/null 2>&1
docker run -d --name qolqe-perf --cpus=1 --memory=1g -p 8000:8000 -v "$PWD:/perf" qolqe-perf > /dev/null
until curl -sf localhost:8000/api/salud > /dev/null; do sleep 1; done

# datos: un usuario por vu, y la foto de la bd para revisar el dinero al final
docker exec qolqe-perf python /perf/datos/preparar_datos.py "$usuarios"
docker exec qolqe-perf python /perf/verificar_dinero.py antes "/perf/$salida/foto_antes.json"

# cpu y memoria de qolqe (dentro del contenedor) y de k6 (en la laptop)
docker exec -d qolqe-perf python /perf/monitor.py 1 "/perf/$salida/recursos_qolqe.csv"
echo "inicio $(date '+%Y-%m-%d %H:%M:%S')" > "$salida/horario.txt"

K6_WEB_DASHBOARD=true K6_WEB_DASHBOARD_EXPORT="$salida/reporte.html" \
  k6 run --out "csv=$salida/metricas.csv.gz" --summary-export "$salida/resumen_k6.json" \
  "escenarios/$prueba.js" 2>&1 | tee "$salida/salida.txt" &
fin_k6=$!
sleep 2
$py monitor.py "$(pgrep -n -x k6)" "$salida/recursos_k6.csv" &
wait $fin_k6

echo "fin    $(date '+%Y-%m-%d %H:%M:%S')" >> "$salida/horario.txt"
touch "$salida/recursos_qolqe.csv.fin" "$salida/recursos_k6.csv.fin"
sleep 3 && rm -f "$salida"/*.fin

docker exec qolqe-perf python /perf/verificar_dinero.py despues "/perf/$salida/foto_antes.json" \
  "/perf/$salida/resumen_k6.json" "/perf/$salida/integridad.txt"
docker logs qolqe-perf 2>&1 | gzip > "$salida/log_qolqe.txt.gz"
# con miles de "Request Failed" la salida de k6 pesa megas: se guarda comprimida
[ "$(wc -c < "$salida/salida.txt")" -gt 1000000 ] && gzip -f "$salida/salida.txt"
$py graficos.py "$salida"
