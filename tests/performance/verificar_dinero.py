# revisa que ninguna operacion de dinero quede a medias ni se aplique dos veces.
# compara la bd antes y despues de la prueba y la cruza con los 201 que conto k6.
# corre dentro del contenedor (lee la bd de qolqe, no la modifica):
#   python verificar_dinero.py antes <foto.json>
#   python verificar_dinero.py despues <foto.json> <resumen_k6.json> <integridad.txt>
import json
import sqlite3
import sys

BD = "file:/app/datos/qolqe.db?mode=ro"
TABLAS = ["movimientos", "transferencias", "recargas", "pagos_servicio"]


def conectar():
    bd = sqlite3.connect(BD, uri=True, timeout=30)
    bd.row_factory = sqlite3.Row
    return bd


def foto(bd):
    return {
        "max_id": {t: bd.execute(f"SELECT COALESCE(MAX(id), 0) FROM {t}").fetchone()[0] for t in TABLAS},
        "saldos": {str(f[0]): f[1] for f in bd.execute("SELECT usuario_id, saldo_cent FROM cuentas")},
    }


def revisar(bd, antes, resumen_k6):
    desde = antes["max_id"]
    resultados = []

    def anotar(nombre, ok, detalle):
        resultados.append((nombre, ok, detalle))

    # 1. cada transferencia nueva tiene exactamente su salida y su entrada
    transferencias = bd.execute("SELECT * FROM transferencias WHERE id > ? AND tipo = 'QOLQE'",
                                (desde["transferencias"],)).fetchall()
    rotas = 0
    for t in transferencias:
        salida = bd.execute("SELECT COUNT(*) FROM movimientos WHERE id > ? AND codigo_operacion = ? "
                            "AND usuario_id = ? AND tipo = 'TRANSFERENCIA_ENVIADA'",
                            (desde["movimientos"], t["codigo_operacion"], t["origen_id"])).fetchone()[0]
        entrada = bd.execute("SELECT COUNT(*) FROM movimientos WHERE id > ? AND codigo_operacion = ? "
                             "AND usuario_id = ? AND tipo = 'TRANSFERENCIA_RECIBIDA'",
                             (desde["movimientos"], t["codigo_operacion"], t["destino_id"])).fetchone()[0]
        if salida != 1 or entrada != 1:
            rotas += 1
    anotar("transferencias con salida y entrada", rotas == 0,
           f"{len(transferencias)} transferencias, {rotas} con movimientos que no cuadran")

    # 2. el saldo de cada cuenta cambio exactamente lo que dicen sus movimientos nuevos
    movido = dict(bd.execute("SELECT usuario_id, SUM(importe_cent) FROM movimientos WHERE id > ? "
                             "GROUP BY usuario_id", (desde["movimientos"],)).fetchall())
    descuadres = []
    for usuario_id, saldo in bd.execute("SELECT usuario_id, saldo_cent FROM cuentas"):
        antes_cent = antes["saldos"].get(str(usuario_id), 0)
        if saldo - antes_cent != movido.get(usuario_id, 0):
            descuadres.append(usuario_id)
    anotar("saldo = saldo anterior + movimientos", not descuadres,
           f"{len(descuadres)} cuentas descuadradas {descuadres[:10]}")

    # 3. ninguna deuda pagada dos veces
    dobles = bd.execute("SELECT COUNT(*) FROM (SELECT deuda_id FROM pagos_servicio WHERE id > ? "
                        "GROUP BY deuda_id HAVING COUNT(*) > 1)", (desde["pagos_servicio"],)).fetchone()[0]
    anotar("deudas pagadas una sola vez", dobles == 0, f"{dobles} deudas con mas de un pago")

    # 4. codigos de operacion repetidos entre operaciones distintas
    repetidos = 0
    for tabla in ["transferencias", "recargas", "pagos_servicio"]:
        repetidos += bd.execute(f"SELECT COUNT(*) FROM (SELECT codigo_operacion FROM {tabla} WHERE id > ? "
                                "GROUP BY codigo_operacion HAVING COUNT(*) > 1)", (desde[tabla],)).fetchone()[0]
    anotar("codigos de operacion unicos", repetidos == 0, f"{repetidos} codigos repetidos")

    # 5. ningun saldo negativo
    negativos = bd.execute("SELECT COUNT(*) FROM cuentas WHERE saldo_cent < 0").fetchone()[0]
    anotar("sin saldos negativos", negativos == 0, f"{negativos} cuentas en negativo")

    # 6. la bd tiene las mismas operaciones que k6 recibio con 201
    en_bd = sum(bd.execute(f"SELECT COUNT(*) FROM {t} WHERE id > ?", (desde[t],)).fetchone()[0]
                for t in ["transferencias", "recargas", "pagos_servicio"])
    con_201 = resumen_k6["metrics"].get("dinero_ok", {}).get("count", 0)
    anotar("operaciones en la bd = 201 recibidos por k6", en_bd == con_201,
           f"bd: {en_bd}, k6: {con_201}")
    return resultados


if sys.argv[1] == "antes":
    with open(sys.argv[2], "w") as f:
        json.dump(foto(conectar()), f)
else:
    with open(sys.argv[2]) as f:
        antes = json.load(f)
    with open(sys.argv[3]) as f:
        resumen_k6 = json.load(f)
    resultados = revisar(conectar(), antes, resumen_k6)
    lineas = [f"{'OK   ' if ok else 'FALLA'} {nombre}: {detalle}" for nombre, ok, detalle in resultados]
    with open(sys.argv[4], "w") as f:
        f.write("\n".join(lineas) + "\n")
    print("\n".join(lineas))
