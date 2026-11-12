# prepara los datos de prueba: un usuario distinto por vu, con saldo y deudas propias.
# corre dentro del contenedor porque escribe las deudas directo en la bd:
#   docker exec qolqe-perf python /perf/datos/preparar_datos.py 1000
import csv
import json
import sqlite3
import sys
import urllib.request
from datetime import date, datetime, timedelta

URL = "http://localhost:8000"
BD = "/app/datos/qolqe.db"
PIN = "2580"           # el de los usuarios de carga de la semilla
SALDO = 10000          # S/ por usuario, sobra para toda una prueba
DEUDAS = 20            # suministros por usuario, cada uno con una deuda pendiente
CONTACTOS = 5          # los 5 usuarios siguientes, para ver y buscar contactos
USUARIOS_SEMILLA = 200  # la semilla ya trae 900000001 a 900000200


def llamar(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    pedido = urllib.request.Request(URL + ruta, data=datos, method=metodo,
                                    headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(pedido) as respuesta:
        return respuesta.status


def celular(n):
    return f"9{n:08d}"


def suministros(n):
    return [f"5{n:06d}{k:02d}" for k in range(DEUDAS)]


total = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

# datos semilla y reloj real
llamar("DELETE", "/api/pruebas/reloj")
llamar("POST", "/api/pruebas/reiniciar")

# usuarios que faltan, por el mismo registro que usa la app
for n in range(USUARIOS_SEMILLA + 1, total + 1):
    llamar("POST", "/api/usuarios", {"dni": f"7{n:07d}", "nombres": f"Usuario Carga {n:04d}",
                                     "celular": celular(n), "pin": PIN})

# el mismo saldo para todos
for n in range(1, total + 1):
    llamar("PUT", "/api/pruebas/saldo", {"celular": celular(n), "saldo": SALDO})

# la app no tiene endpoint para crear deudas: se insertan en la bd
vence = date.today() + timedelta(days=10)
filas = [("AGUA", s, f"Usuario Carga {n:04d}", f"{vence:%Y-%m}", 5000 + n % 100 * 10, vence.isoformat())
         for n in range(1, total + 1) for s in suministros(n)]
bd = sqlite3.connect(BD, timeout=30)
bd.executemany("INSERT INTO deudas (empresa, suministro, titular, periodo, monto_cent, vencimiento) "
               "VALUES (?, ?, ?, ?, ?, ?)", filas)

# contactos tambien por la bd: son solo para que la lista no salga vacia
ids = dict(bd.execute("SELECT celular, id FROM usuarios WHERE celular LIKE '9000%'").fetchall())
contactos = [(ids[celular(n)], ids[celular(m)], f"Carga {m:04d}", 0, datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
             for n in range(1, total + 1) for m in range(n + 1, n + 1 + CONTACTOS) if celular(m) in ids]
bd.executemany("INSERT INTO contactos (usuario_id, contacto_usuario_id, alias, favorito, creado_en) "
               "VALUES (?, ?, ?, ?, ?)", contactos)
bd.commit()
bd.close()

with open("/perf/datos/usuarios.csv", "w", newline="") as archivo:
    escritor = csv.writer(archivo)
    escritor.writerow(["celular", "pin", "suministros"])
    for n in range(1, total + 1):
        escritor.writerow([celular(n), PIN, ";".join(suministros(n))])

print(f"{total} usuarios con S/ {SALDO}, {DEUDAS} deudas y {CONTACTOS} contactos cada uno -> datos/usuarios.csv")
