# graficos y tablas de una prueba a partir de lo que deja correr.sh
# uso: python graficos.py resultados/<prueba>
import csv
import gzip
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

carpeta = Path(sys.argv[1])
prueba = carpeta.name
TRAMO = 30  # segundos por punto en los graficos
UMBRAL = {"consulta": 800, "dinero": 1500}
UMBRAL_CAMPANA = {"consulta": 1600, "dinero": 3000}


def p(valores, percentil):
    # como en clase: ordenar y leer la posicion
    if not valores:
        return math.nan
    orden = sorted(valores)
    return orden[max(0, math.ceil(percentil / 100 * len(orden)) - 1)]


def etiquetas(texto):
    return dict(par.split("=", 1) for par in texto.split("&") if "=" in par)


# ---------------------------------------------------------------- lectura

pedidos = []  # (segundo, op, tipo, ms, fallo)
vus = {}  # segundo -> vus
sesiones = []
negocio = defaultdict(int)
with gzip.open(carpeta / "metricas.csv.gz", "rt") as f:
    for fila in csv.DictReader(f):
        nombre, t, valor = fila["metric_name"], int(fila["timestamp"]), float(fila["metric_value"])
        tags = etiquetas(fila["extra_tags"])
        if nombre == "http_req_duration":
            pedidos.append([t, tags.get("op"), tags.get("tipo"), valor, None])
        elif nombre == "http_req_failed":
            pedidos[-1][4] = valor == 1  # k6 escribe failed justo despues de duration
        elif nombre == "vus":
            vus[t] = int(valor)
        elif nombre == "sesiones":
            sesiones.append(t)
        elif nombre == "errores_negocio":
            negocio[(tags.get("op"), tags.get("codigo"))] += 1


def leer_recursos(nombre):
    ruta = carpeta / nombre
    if not ruta.exists():
        return []
    with open(ruta) as f:
        return [(int(r["epoch"]), float(r["cpu_%"]), float(r["memoria_MB"]), int(r.get("hilos") or 0))
                for r in csv.DictReader(f)]


qolqe = leer_recursos("recursos_qolqe.csv")
k6 = leer_recursos("recursos_k6.csv")
inicio = min(vus)

# ---------------------------------------------------------------- series por tramo de 30 s

def tramo(t):
    return (t - inicio) // TRAMO


series = defaultdict(lambda: {"consulta": [], "dinero": [], "n": 0, "fallos": 0, "vus": 0,
                              "cpu": [], "mem": [], "cpu_k6": [], "hilos": []})
for t, op, tipo, ms, fallo in pedidos:
    s = series[tramo(t)]
    s[tipo].append(ms)
    s["n"] += 1
    s["fallos"] += bool(fallo)
for t, v in vus.items():
    series[tramo(t)]["vus"] = max(series[tramo(t)]["vus"], v)
for t, cpu, mem, hilos in qolqe:
    if t >= inicio:
        series[tramo(t)]["cpu"].append(cpu)
        series[tramo(t)]["mem"].append(mem)
        series[tramo(t)]["hilos"].append(hilos)
for t, cpu, _, _ in k6:
    if t >= inicio:
        series[tramo(t)]["cpu_k6"].append(cpu)

claves = sorted(k for k in series if k * TRAMO <= max(vus) - inicio)
minutos = [(k * TRAMO + TRAMO / 2) / 60 for k in claves]


def serie(funcion):
    return [funcion(series[k]) for k in claves]


def promedio(lista):
    return sum(lista) / len(lista) if lista else math.nan


hay_hilos = any(r[3] for r in qolqe)
fig, ejes = plt.subplots(5 if hay_hilos else 4, 1, figsize=(11, 14 if hay_hilos else 12), sharex=True)
fig.suptitle(f"Qolqe Wallet · prueba de {prueba}", fontsize=14, x=0.07, ha="left")

ax = ejes[0]
ax.plot(minutos, serie(lambda s: s["vus"]), color="#4b5563")
ax.set_ylabel("usuarios virtuales")

ax = ejes[1]
ax.plot(minutos, serie(lambda s: p(s["consulta"], 95)), color="#2563eb", label="p95 consultas y login")
ax.plot(minutos, serie(lambda s: p(s["dinero"], 95)), color="#ea580c", label="p95 operaciones de dinero")
ax.axhline(UMBRAL["consulta"], color="#2563eb", ls="--", lw=1, label="umbral consultas 800 ms")
ax.axhline(UMBRAL["dinero"], color="#ea580c", ls="--", lw=1, label="umbral dinero 1500 ms")
if prueba == "pico":
    ax.axhline(UMBRAL_CAMPANA["consulta"], color="#2563eb", ls=":", lw=1, label="campaña consultas 1600 ms")
    ax.axhline(UMBRAL_CAMPANA["dinero"], color="#ea580c", ls=":", lw=1, label="campaña dinero 3000 ms")
ax.set_ylabel("tiempo de respuesta (ms)")
if max(p(s["consulta"] + s["dinero"], 95) for s in series.values() if s["n"]) > 5000:
    ax.set_yscale("log")  # con timeouts de 60 s, en escala normal los ms quedan pegados al cero
ax.legend(fontsize=8, loc="upper left")

ax = ejes[2]
ax.plot(minutos, serie(lambda s: s["n"] / TRAMO), color="#059669", label="peticiones por segundo")
ax.set_ylabel("peticiones/s")
ax2 = ax.twinx()
ax2.plot(minutos, serie(lambda s: 100 * s["fallos"] / s["n"] if s["n"] else 0), color="#dc2626", label="errores %")
ax2.axhline(1, color="#dc2626", ls="--", lw=1)
ax2.set_ylabel("errores (%)", color="#dc2626")
ax.legend(fontsize=8, loc="upper left")
ax2.legend(fontsize=8, loc="upper right")

ax = ejes[3]
ax.plot(minutos, serie(lambda s: promedio(s["cpu"])), color="#059669", label="CPU Qolqe (límite 100 %)")
ax.plot(minutos, serie(lambda s: promedio(s["cpu_k6"])), color="#a16207", label="CPU k6 (% de 1 núcleo)")
ax.axhline(80, color="#a16207", ls="--", lw=1, label="k6 válido hasta 80 %")
ax.set_ylabel("CPU (%)")
ax2 = ax.twinx()
ax2.plot(minutos, serie(lambda s: max(s["mem"]) if s["mem"] else math.nan), color="#7c3aed", label="memoria Qolqe")
ax2.set_ylabel("memoria (MB)", color="#7c3aed")
ax2.set_ylim(0, max(r[2] for r in qolqe) * 1.25)  # desde 0: en escala ajustada 2 MB parecen una fuga
ax.legend(fontsize=8, loc="upper left")
ax2.legend(fontsize=8, loc="upper right")

if hay_hilos:
    ax = ejes[4]
    ax.plot(minutos, serie(lambda s: max(s["hilos"]) if s["hilos"] else math.nan), color="#4b5563", label="hilos de Qolqe")
    base = min(r[3] for r in qolqe if r[3])
    ax.axhline(base + 40, color="#dc2626", ls="--", lw=1, label=f"pool lleno: {base} hilos base + 40 del pool de FastAPI")
    ax.set_ylabel("hilos")
    ax.legend(fontsize=8, loc="upper left")
ejes[-1].set_xlabel("minutos desde el inicio")

for ax in ejes:
    ax.grid(alpha=0.25)
    ax.spines[["top"]].set_visible(False)
fig.tight_layout()
fig.savefig(carpeta / "graficos.png", dpi=130)

# ---------------------------------------------------------------- tablas

def tramos_estables():
    """Intervalos de al menos 90 s con los mismos vus (las mesetas de cada escenario)."""
    segundos = sorted(vus)
    grupos, actual = [], [segundos[0]]
    for t in segundos[1:]:
        if vus[t] == vus[actual[0]] and t - actual[-1] <= 2:
            actual.append(t)
        else:
            grupos.append(actual)
            actual = [t]
    grupos.append(actual)
    return [(g[0], g[-1], vus[g[0]]) for g in grupos if g[-1] - g[0] >= 90 and vus[g[0]] > 0]


def fila_tramo(desde, hasta, n_vus):
    dentro = [x for x in pedidos if desde <= x[0] <= hasta]
    duracion = hasta - desde + 1
    consulta = [x[3] for x in dentro if x[2] == "consulta"]
    dinero = [x[3] for x in dentro if x[2] == "dinero"]
    login = [x[3] for x in dentro if x[1] == "login"]
    fallos = sum(1 for x in dentro if x[4])
    ses = sum(1 for t in sesiones if desde <= t <= hasta)
    cpu = [r[1] for r in qolqe if desde <= r[0] <= hasta]
    mem = [r[2] for r in qolqe if desde <= r[0] <= hasta]
    hilos = [r[3] for r in qolqe if desde <= r[0] <= hasta]
    cpu_k6 = [r[1] for r in k6 if desde <= r[0] <= hasta]
    return [f"{(desde - inicio) / 60:.1f}–{(hasta - inicio) / 60:.1f}", n_vus, len(dentro),
            f"{len(dentro) / duracion:.1f}", f"{ses / duracion * 60:.1f}",
            f"{p(login, 95):.0f}", f"{p(consulta, 95):.0f}", f"{p(dinero, 95):.0f}",
            f"{100 * fallos / max(1, len(dentro)):.2f}",
            f"{promedio(cpu):.0f} / {max(cpu, default=math.nan):.0f}",
            f"{max(mem, default=math.nan):.0f}", f"{max(hilos, default=0)}", f"{max(cpu_k6, default=math.nan):.0f}"]


def tabla(encabezado, filas):
    lineas = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    lineas += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(lineas)


texto = [f"# Prueba de {prueba}", ""]
horario = carpeta / "horario.txt"
if horario.exists():
    texto += ["```", horario.read_text().strip(), "```", ""]

texto += ["## Por tramo estable (mismos VUs al menos 90 s)", "",
          tabla(["minutos", "VUs", "peticiones", "pet/s", "sesiones/min", "p95 login", "p95 consultas",
                 "p95 dinero", "errores %", "CPU Qolqe prom / máx", "memoria máx MB", "hilos máx", "CPU k6 máx"],
                [fila_tramo(*t) for t in tramos_estables()]),
          "", "Tiempos en ms. Umbrales de hora punta: consultas y login p95 < 800, dinero p95 < 1500, errores < 1 %.", ""]

# mesetas largas en ventanas de 5 min: si el p95 o la memoria suben con el tiempo, se acumulan retrasos
ventanas = []
for desde, hasta, n_vus in tramos_estables():
    if hasta - desde >= 15 * 60:
        for v in range(desde, hasta - 298, 300):  # solo ventanas completas
            ventanas.append(fila_tramo(v, v + 299, n_vus))
if ventanas:
    texto += ["## Mesetas largas, cada 5 minutos", "",
              tabla(["minutos", "VUs", "peticiones", "pet/s", "sesiones/min", "p95 login", "p95 consultas",
                     "p95 dinero", "errores %", "CPU Qolqe prom / máx", "memoria máx MB", "hilos máx", "CPU k6 máx"],
                    ventanas), ""]

filas_op = []
for op in ["login", "saldo_perfil", "movimientos", "contactos", "deudas", "otras", "transferencia", "recarga", "pago"]:
    tiempos = [x[3] for x in pedidos if x[1] == op]
    fallos = sum(1 for x in pedidos if x[1] == op and x[4])
    if tiempos:
        filas_op.append([op, len(tiempos), f"{p(tiempos, 50):.0f}", f"{p(tiempos, 95):.0f}",
                         f"{p(tiempos, 99):.0f}", f"{max(tiempos):.0f}", f"{100 * fallos / len(tiempos):.2f}"])
texto += ["## Por operación (toda la prueba)", "",
          tabla(["operación", "peticiones", "p50", "p95", "p99", "máx", "errores %"], filas_op), ""]

if negocio:
    texto += ["## Rechazos 4xx (reglas de negocio o datos)", "",
              tabla(["operación", "código", "veces"], [[op, c, n] for (op, c), n in sorted(negocio.items())]), ""]

integridad = carpeta / "integridad.txt"
if integridad.exists():
    texto += ["## Dinero: antes y después", "", "```", integridad.read_text().strip(), "```", ""]

datos = {"tramos": [fila_tramo(*t) for t in tramos_estables()], "ventanas": ventanas, "operaciones": filas_op,
         "negocio": [[op, c, n] for (op, c), n in sorted(negocio.items())],
         "integridad": integridad.read_text().splitlines() if integridad.exists() else []}

# ---------------------------------------------------------------- capacidad: un punto por escalon

escalones = tramos_estables()
if len(escalones) < 3 and max(vus.values()) >= 500:
    # subida continua (sondeo): franjas de 100 vus en vez de mesetas
    franjas = defaultdict(list)
    cima = max(vus, key=lambda t: vus[t])
    for t in sorted(vus):
        if t <= cima:  # solo la subida
            franjas[vus[t] // 100 * 100].append(t)
    escalones = [(min(ts), max(ts), banda) for banda, ts in sorted(franjas.items()) if banda > 0 and len(ts) >= 20]
    filas = [fila_tramo(*t) for t in escalones]
    texto += ["## Por franja de 100 VUs (subida continua)", "",
              tabla(["minutos", "VUs desde", "peticiones", "pet/s", "sesiones/min", "p95 login", "p95 consultas",
                     "p95 dinero", "errores %", "CPU Qolqe prom / máx", "memoria máx MB", "hilos máx", "CPU k6 máx"],
                    filas), ""]
    datos["franjas"] = filas
if len(escalones) >= 3:
    puntos = []
    for desde, hasta, n_vus in escalones:
        dentro = [x for x in pedidos if desde <= x[0] <= hasta]
        puntos.append((n_vus,
                       p([x[3] for x in dentro if x[2] == "consulta"], 95),
                       p([x[3] for x in dentro if x[2] == "dinero"], 95),
                       100 * sum(1 for x in dentro if x[4]) / max(1, len(dentro)),
                       promedio([r[1] for r in qolqe if desde <= r[0] <= hasta])))
    x = [pt[0] for pt in puntos]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2))
    a1.plot(x, [pt[1] for pt in puntos], "o-", color="#2563eb", label="p95 consultas y login")
    a1.plot(x, [pt[2] for pt in puntos], "o-", color="#ea580c", label="p95 dinero")
    a1.axhline(UMBRAL["consulta"], color="#2563eb", ls="--", lw=1)
    a1.axhline(UMBRAL["dinero"], color="#ea580c", ls="--", lw=1)
    a1.set_xlabel("usuarios virtuales del escalón")
    a1.set_ylabel("p95 (ms)")
    if max(pt[1] for pt in puntos) > 5000:
        a1.set_yscale("log")
    a1.legend(fontsize=8)
    a2.plot(x, [pt[4] for pt in puntos], "o-", color="#059669", label="CPU Qolqe promedio %")
    a2.plot(x, [pt[3] for pt in puntos], "o-", color="#dc2626", label="errores %")
    a2.axhline(1, color="#dc2626", ls="--", lw=1)
    a2.set_xlabel("usuarios virtuales del escalón")
    a2.legend(fontsize=8)
    for ax in (a1, a2):
        ax.grid(alpha=0.25)
        ax.spines[["top", "right"]].set_visible(False)
    detalle = "cada punto es una meseta" if len(tramos_estables()) >= 3 else "cada punto es una franja de 100 VUs"
    fig.suptitle(f"Qolqe Wallet · {prueba}: {detalle}", fontsize=12, x=0.07, ha="left")
    fig.tight_layout()
    fig.savefig(carpeta / "capacidad.png", dpi=130)

(carpeta / "resumen.md").write_text("\n".join(texto))
(carpeta / "metricas.json").write_text(json.dumps(datos, ensure_ascii=False, indent=1))
print("\n".join(texto))
