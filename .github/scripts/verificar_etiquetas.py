"""Primera etapa del pipeline: la trazabilidad de los .feature está completa antes de correr nada.

Uso: python .github/scripts/verificar_etiquetas.py

Revisa:
  - cada escenario tiene un @CP-NN propio (sin repetir entre archivos);
  - cada escenario de API tiene su @HU y sus criterios @CA-<mod>-<hu>-<n> (p. ej. @CA-N-07-3 = HU-N-07 CA3),
    y cada criterio existe en docs/requisitos.md y es de una HU del mismo escenario;
  - cada fallo esperado (@fail en API, @defecto en web) dice qué defecto lo causa (@DEF-NN) y ese defecto
    está en docs/defectos.md;
  - cada criterio del núcleo y de G5 tiene al menos un escenario de API, salvo los excluidos abajo con su motivo.
Sale con error y la lista de problemas si algo falta.
"""
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario|Esquema del escenario|Escenario):\s*(.+)$")
FEATURE = re.compile(r"^\s*(Feature|Característica):")
EJEMPLOS = re.compile(r"^\s*(Examples|Scenarios|Ejemplos):")
CA_TAG = re.compile(r"^CA-(N|G\d+)-(\d+)-(\d+)$")

# criterios que no se pueden verificar por la API de este módulo
SIN_ESCENARIO: dict[str, str] = {}


def criterios_requisitos():
    """{'HU-N-07': {1, 2, 3, ...}} de docs/requisitos.md."""
    criterios, hu = {}, None
    for linea in (RAIZ / "docs/requisitos.md").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^### (HU-[A-Z0-9]+-\d+) ", linea):
            hu = m.group(1)
            criterios[hu] = set()
        elif hu and (m := re.match(r"^- \*\*CA(\d+)\.\*\*", linea)):
            criterios[hu].add(int(m.group(1)))
    return criterios


def escenarios():
    """Lista de (archivo, línea, nombre, etiquetas del escenario + feature, etiquetas de sus Examples)."""
    lista = []
    for archivo in sorted((RAIZ / "features").rglob("*.feature")):
        de_feature, pendientes, actual = [], [], None
        for n, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), 1):
            texto = linea.strip()
            if texto.startswith("@"):
                pendientes += [t[1:] for t in texto.split() if t.startswith("@")]
            elif FEATURE.match(linea):
                de_feature, pendientes = pendientes, []
            elif m := ESCENARIO.match(linea):
                actual = [archivo.relative_to(RAIZ).as_posix(), n, m.group(2).strip(), de_feature + pendientes, []]
                lista.append(actual)
                pendientes = []
            elif EJEMPLOS.match(linea):
                if actual:
                    actual[4] += pendientes
                pendientes = []
            elif texto and not texto.startswith("#"):
                pendientes = []
    return lista


def main():
    requisitos = criterios_requisitos()
    defectos = set(re.findall(r"^## (DEF-\d+):", (RAIZ / "docs/defectos.md").read_text(encoding="utf-8"), re.M))
    problemas, vistos, cubiertos = [], {}, set()

    for archivo, linea, nombre, etiquetas, de_ejemplos in escenarios():
        donde = f"{archivo}:{linea} «{nombre}»"
        es_api = not archivo.startswith("features/ui/")
        cps = [t for t in etiquetas if t.startswith("CP-")]
        hus = [t for t in etiquetas if t.startswith("HU-")]
        defs = [t for t in etiquetas + de_ejemplos if t.startswith("DEF-")]

        if len(cps) != 1:
            problemas.append(f"{donde}: debe tener un solo @CP-NN (tiene {len(cps)})")
        elif cps[0] in vistos:
            problemas.append(f"{donde}: {cps[0]} repetido (también en {vistos[cps[0]]})")
        else:
            vistos[cps[0]] = donde
        for hu in hus:
            if hu not in requisitos:
                problemas.append(f"{donde}: @{hu} no está en docs/requisitos.md")
        if es_api and not hus:
            problemas.append(f"{donde}: falta la @HU que cubre")

        cas = [t for t in etiquetas if t.startswith("CA-")]
        if es_api and hus and not cas:
            problemas.append(f"{donde}: falta el criterio que cubre (@CA-...)")
        for ca in cas:
            m = CA_TAG.match(ca)
            hu = m and f"HU-{m.group(1)}-{m.group(2)}"
            if not m or hu not in requisitos or int(m.group(3)) not in requisitos[hu]:
                problemas.append(f"{donde}: @{ca} no corresponde a un criterio de docs/requisitos.md")
            elif hu not in hus:
                problemas.append(f"{donde}: @{ca} es de {hu}, pero el escenario no tiene @{hu}")
            elif es_api:
                cubiertos.add(f"{hu} CA{m.group(3)}")

        esperado = "fail" in etiquetas + de_ejemplos or "defecto" in etiquetas
        if esperado and not defs:
            problemas.append(f"{donde}: fallo esperado sin @DEF-NN")
        for d in defs:
            if d not in defectos:
                problemas.append(f"{donde}: @{d} no está en docs/defectos.md")

    modulos = {"HU-N", "HU-G5"}
    for hu, cas in requisitos.items():
        if hu.rsplit("-", 1)[0] not in modulos:
            continue
        for n in sorted(cas):
            clave = f"{hu} CA{n}"
            if clave not in cubiertos and clave not in SIN_ESCENARIO:
                problemas.append(f"{clave}: ningún escenario de API lo cubre")

    if problemas:
        print(f"Trazabilidad incompleta ({len(problemas)}):")
        print("\n".join(f"  - {p}" for p in problemas))
        sys.exit(1)
    total = sum(len(c) for h, c in requisitos.items() if h.rsplit("-", 1)[0] in modulos)
    excluidos = "; ".join(f"{k}: {v}" for k, v in SIN_ESCENARIO.items())
    print(f"Trazabilidad completa: {len(vistos)} escenarios, {len(cubiertos)} de {total} criterios con escenario de API"
          + (f" (excluidos: {excluidos})" if excluidos else ""))


if __name__ == "__main__":
    main()
