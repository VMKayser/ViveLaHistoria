#!/usr/bin/env python3
"""Clasifica cada archivo del repositorio anterior en un PR de la migración o en una exclusión con motivo.

Uso (desde la raíz de un clon del repositorio ANTERIOR):  python3 -I migracion/clasificar.py
Salida: migracion/manifiesto.json (fuente única para incorporar.sh y auditar.py).
"""
import json, re, subprocess, sys
from pathlib import Path

ORIGEN_COMMIT = "9461982505ec6e4305ca25194b21c896bb1a9e0a"   # main del repo anterior (2026-11-27 09:18)
DEVELOP_COMMIT = "452a364b5c776da19c51c666aba865da8889775b"  # trae museo_interior/README.md
REPO_ANTERIOR = "git@github.com:ManuelRuaEchalar/miCiudadCharcas.git"

# Exclusiones: (expresión, motivo). Se evalúan antes que las reglas de inclusión.
EXCLUIR = [
    (r"^fotosCentro/", "fotografías de referencia"),
    (r"^fotos/", "fotografías de referencia"),
    (r"^Peatonal/", "capturas de referencia (solo citadas en comentarios)"),
    (r"^guia_plaza/", "fotografías de referencia"),
    (r"^SucreAesthetic(Aplied)?/", "pruebas de estilo con rutas locales"),
    (r"^piloto_estilos/", "pruebas de estilo descartadas"),
    (r"^capturas/", "capturas de pantalla"),
    (r"^secciones/", "notas de trabajo"),
    (r"^coordinacion/(?!revisiones/LEEME\.md$)", "coordinación interna y correcciones con capturas"),
    (r"^contenido/libro/", "texto de investigación (libro de referencia)"),
    (r"^museo_interior/referencias", "fotografías de referencia del museo"),
    (r"^web/public/models/ciudad/[^/]+/(personajes|vehiculos)/.*\.(html|bundle\.js|png|jpg)$", "visores y vistas previas de trabajo"),
    (r"^blender/zonas/codex/(avances_\d+/|propuesta_.*\.patch$)", "entregas temporales de trabajo"),
    (r"^(AGENTS|CLAUDE)\.md$", "reemplazado por las instrucciones nuevas"),
    (r"^README\.md$", "reemplazado: el README nuevo cubre todo el proyecto"),
    (r"^\.gitignore$", "reemplazado por el .gitignore nuevo (PR01)"),
    (r"^\.claude/", "enlaces simbólicos a .agents/skills (no hacen falta)"),
    (r"^[^/]+\.(pdf|docx|zip|html|png)$", "documentos, anuncios e imágenes sueltas de la raíz"),
]

# Inclusión: (expresión, PR). Gana la primera que coincide.
REGLAS = [
    # PR02 · web: base y portada
    (r"^web/src/(ciudad/revision|app/api|servidor)/", "PR11"),
    (r"^web/src/(ciudad/|app/ciudad/)", "PR05"),
    (r"^web/public/(trafico)/", "PR06"),
    (r"^web/scripts/(preparar_vehiculos\.mjs|red_vial.*|vehiculos_trafico\.json)$", "PR06"),
    (r"^web/public/models/ciudad/[^/]+/personajes/", "PR07"),
    (r"^web/public/models/ciudad/[^/]+/vehiculos/", "PR06"),
    (r"^web/public/models/", "PR04"),
    (r"^web/public/(mapa|fotos)/", "PR03"),
    (r"^web/", "PR02"),
    (r"^banderaSucre\.png$", "PR02"),
    # PR03 · datos urbanos y pipeline de modelado
    (r"^(Sucre\.osm\..*|urban-export_.*\.fbx)$", "PR03"),
    (r"^(reparto|estilo)/", "PR03"),
    (r"^scripts/revisiones\.py$", "PR11"),
    (r"^scripts/", "PR03"),
    (r"^blender/(kit|scripts|secciones)/", "PR03"),
    (r"^blender/zonas/PLANTILLA\.py$", "PR03"),
    (r"^\.agents/skills/vehiculo-3d-desde-diseno/", "PR06"),
    (r"^\.agents/", "PR03"),
    (r"^recursos/", "PR03"),
    # PR04 · modelos de la ciudad (scripts de manzanas)
    (r"^blender/zonas/[^/]+/personajes/", "PR07"),
    (r"^blender/zonas/[^/]+/vehiculos/", "PR06"),
    (r"^blender/zonas/", "PR04"),
    # PR10 · Ciudad Charcas 1809
    (r"^godot/", "PR10"),
    (r"^blender/(construir|personajes)_1809\.py$", "PR10"),
    (r"^herramientas/", "PR10"),
    # PR06 · tráfico
    (r"^autos/", "PR06"),
    (r"^ciudad3d/vehiculos/", "PR06"),
    (r"^ciudad3d/scripts/trafico", "PR06"),
    (r"^ciudad3d/herramientas/vehiculos\.mjs$", "PR06"),
    # PR07 · personajes y animaciones / PR08 · encuentros y voces
    (r"^ciudad3d/scripts/personajes/(carta|encuentros|voz)\.gd", "PR08"),
    (r"^ciudad3d/herramientas/audio_encuentros\.py$", "PR08"),
    (r"^ciudad3d/personajes/(ui|herramientas)/", "PR08"),
    (r"^personas/encuentros/", "PR08"),
    (r"^contenido/(?!personajes\.json$)", "PR08"),
    (r"^ciudad3d/personajes/", "PR07"),
    (r"^ciudad3d/scripts/personajes/", "PR07"),
    (r"^ciudad3d/herramientas/(personajes|cabezas)\.py$", "PR07"),
    (r"^personas/", "PR07"),
    (r"^contenido/personajes\.json$", "PR07"),
    # PR09 · museo y escenas históricas
    (r"^museo_interior/", "PR09"),
    (r"^ciudad3d/(escenas_historicas|escape_rooms)/", "PR09"),
    # PR11 · revisiones y app móvil
    (r"^coordinacion/revisiones/LEEME\.md$", "PR11"),
    (r"^movil/", "PR11"),
    # PR05 · motor de la ciudad 3D (todo lo demás de ciudad3d)
    (r"^ciudad3d/", "PR05"),
]

# Archivos que no están en el commit de origen pero hacen falta.
EXTRA = [
    {"ruta": "docs/CIUDAD_CHARCAS_1809.md", "pr": "PR10", "fuente": f"git:{ORIGEN_COMMIT}", "desde": "README.md",
     "nota": "README del repo anterior (historia 1809), sin cambios"},
    {"ruta": "docs/REGLAS_MODELADO.md", "pr": "PR03", "fuente": f"git:{ORIGEN_COMMIT}", "desde": "AGENTS.md",
     "nota": "reglas de modelado del repo anterior (citadas por .agents/skills), sin cambios"},
    {"ruta": "museo_interior/README.md", "pr": "PR09", "fuente": f"git:{DEVELOP_COMMIT}"},
    {"ruta": "web/public/mapa/raw/lienzo.glb", "pr": "PR03", "fuente": "local:ManuelRUa",
     "nota": "solo existe en el equipo de ManuelRUa (ignorado en el repo anterior); lo necesita ciudad3d/herramientas/empaquetar.py"},
]


def main():
    salida = subprocess.run(["git", "ls-tree", "-r", "-l", "-z", ORIGEN_COMMIT], capture_output=True, text=True, check=True).stdout
    archivos, excluidos, sin_regla = [], [], []
    for linea in filter(None, salida.split("\0")):
        meta, ruta = linea.split("\t", 1)
        modo, _, oid, tam = meta.split()
        motivo = next((m for e, m in EXCLUIR if re.search(e, ruta)), None)
        if motivo:
            excluidos.append({"ruta": ruta, "motivo": motivo, "bytes": int(tam)})
            continue
        pr = next((p for e, p in REGLAS if re.search(e, ruta)), None)
        if pr is None:
            sin_regla.append(ruta)
            continue
        archivos.append({"ruta": ruta, "pr": pr, "oid": oid, "bytes": int(tam), "modo": modo, "fuente": f"git:{ORIGEN_COMMIT}"})
    if sin_regla:
        print("SIN CLASIFICAR:", *sin_regla, sep="\n  ")
        sys.exit(1)
    raiz = Path(__file__).resolve().parents[1]
    for e in EXTRA:
        f = raiz / e["ruta"]
        if e["fuente"].startswith("git:"):
            oid = subprocess.run(["git", "rev-parse", f'{e["fuente"][4:]}:{e.get("desde", e["ruta"])}'], capture_output=True, text=True, check=True).stdout.strip()
            tam = int(subprocess.run(["git", "cat-file", "-s", oid], capture_output=True, text=True).stdout)
        else:
            oid = subprocess.run(["git", "hash-object", str(f)], capture_output=True, text=True, check=True).stdout.strip()
            tam = f.stat().st_size
        archivos.append({**e, "oid": oid, "bytes": tam, "modo": "100644"})
    archivos.sort(key=lambda a: (a["pr"], a["ruta"]))
    resumen = {}
    for a in archivos:
        r = resumen.setdefault(a["pr"], {"archivos": 0, "MB": 0.0})
        r["archivos"] += 1
        r["MB"] = round(r["MB"] + a["bytes"] / 1e6, 1)
    man = {"repo_anterior": REPO_ANTERIOR, "commit_origen": ORIGEN_COMMIT, "commit_develop": DEVELOP_COMMIT,
           "resumen": resumen, "archivos": archivos, "excluidos": excluidos}
    (raiz / "migracion" / "manifiesto.json").write_text(json.dumps(man, ensure_ascii=False, indent=1))
    for pr, r in sorted(resumen.items()):
        print(pr, r)
    print("incluidos", len(archivos), round(sum(a["bytes"] for a in archivos) / 1e6), "MB · excluidos", len(excluidos),
          round(sum(a["bytes"] for a in excluidos) / 1e6), "MB")


if __name__ == "__main__":
    main()
