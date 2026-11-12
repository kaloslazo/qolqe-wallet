# Pruebas de rendimiento (Parte 3)

Pruebas de carga, pico, estrés y resistencia de Qolqe Wallet con [k6](https://grafana.com/docs/k6/latest/), a partir del requerimiento de la campaña «Quincena Qolqe». El análisis completo está en el informe (`docs/Informe_Rendimiento_G5.docx` y la sección 4 de `docs/informe.md`).

## Qué hace falta

- Docker (Qolqe corre en un contenedor con 1 CPU y 1 GB)
- k6 v1 o más nuevo (`brew install k6`)
- El `.venv` del repo con `pip install -r tests/performance/requirements.txt` (psutil y matplotlib)

## Correr una prueba

```bash
docker build -f tests/performance/Dockerfile -t qolqe-perf .   # una vez, desde la raíz
tests/performance/correr.sh carga                              # humo, demo, carga, pico, estres o resistencia
```

El segundo argumento es la cantidad de usuarios a preparar (1000 por defecto; para `demo` alcanza con `100` y la preparación toma segundos). `correr.sh` levanta Qolqe limpio, prepara un usuario por VU, toma la foto de la base, mide CPU, memoria e hilos de Qolqe y de k6 cada segundo, corre k6 y al final revisa el dinero y arma los gráficos. Mientras corre, el panel de k6 está en http://localhost:5665.

El escenario de concurrencia reinicia los datos en cada ronda, por eso va aparte (con Qolqe levantado):

```bash
k6 run tests/performance/escenarios/concurrencia.js
```

## Archivos

```
sesion.js              la sesión de un usuario: login + 6 operaciones con los % del requerimiento
umbrales.js            los umbrales del requerimiento (p95 y tasa de error)
escenarios/            un archivo por prueba: VUs, subida, duración
  humo.js              1 usuario, línea base
  carga.js             hora punta: 100 usuarios, 20 min
  pico.js              campaña: de 100 a 300 usuarios en 5 min, 10 min arriba y vuelta a 100
  estres.js            escalones hasta romper
  resistencia.js       hora punta durante 60 min
  sondeo.js            subida continua de 0 a 2000, solo para ubicar los escalones del estrés
  concurrencia.js      el mismo usuario con varias operaciones de dinero a la vez
  demo.js              carga corta para la exposición
datos/
  preparar_datos.py    reinicia Qolqe, registra los usuarios que faltan, fija saldo, crea deudas y contactos
  usuarios.csv         lo que genera el script: celular, PIN y suministros de cada usuario
monitor.py             CPU, memoria e hilos de un proceso cada segundo (el script del enunciado + hilos)
verificar_dinero.py    compara la base antes y después y la cruza con los 201 de k6
graficos.py            gráficos y tablas por tramo y por operación
resultados/<prueba>/   reporte.html de k6, resumen.md, graficos.png, CSV de recursos, integridad, log
```
