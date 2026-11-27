"""Descarga los assets CC0 de Poly Haven que usa la escena de 1809.

Uso:  python3 -I herramientas/descargar_assets.py
Todo lo de Poly Haven es CC0 (dominio público): https://polyhaven.com/license
Escribe godot/CREDITOS.md con la lista de lo descargado.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "godot" / "assets"
UA = {"User-Agent": "ciudad-charcas-asset-fetch/0.1"}

# id de Poly Haven -> (carpeta local, resolución)
TEXTURAS = {
    "cobblestone_floor_05": ("empedrado", "2k"),
    "white_stucco_02": ("revoque_blanco", "2k"),
    "yellow_plaster_02": ("revoque_ocre", "1k"),
    "clay_roof_tiles_02": ("tejas", "1k"),
    "weathered_brown_planks": ("madera_balcon", "1k"),
    "dark_planks": ("madera_puerta", "1k"),
    "rustic_stone_wall_02": ("piedra", "1k"),
    "stone_tiles_02": ("losa", "1k"),
    "white_rough_plaster": ("piedra_revocada", "1k"),
}
# Mapas que usa Godot (normal en convención OpenGL).
MAPAS = {"Diffuse": "color", "nor_gl": "normal", "arm": "orm"}  # orm = oclusión, rugosidad, metal

CIELOS = {
    "kloppenheim_06_puresky": ("atardecer", "2k"),
    "kloppenheim_02_puresky": ("noche", "2k"),
}

PROPS = ["jug_01", "ceramic_pot", "painted_wooden_bench"]


def pedir_json(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.load(r)


def bajar(url, destino: Path, md5=None):
    if destino.exists() and (md5 is None or hashlib.md5(destino.read_bytes()).hexdigest() == md5):
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        datos = r.read()
    if md5 and hashlib.md5(datos).hexdigest() != md5:
        sys.exit(f"md5 no coincide: {url}")
    destino.write_bytes(datos)
    print(f"  {destino.relative_to(RAIZ.parent)}  ({len(datos) // 1024} KB)")


def main():
    creditos = []
    for pid, (nombre, res) in TEXTURAS.items():
        archivos = pedir_json(f"https://api.polyhaven.com/files/{pid}")
        for mapa, sufijo in MAPAS.items():
            if mapa not in archivos:
                continue
            f = archivos[mapa][res]["jpg"]
            bajar(f["url"], RAIZ / "texturas" / nombre / f"{nombre}_{sufijo}.jpg", f.get("md5"))
        creditos.append(f"- Textura `{nombre}`: [{pid}](https://polyhaven.com/a/{pid})")

    for pid, (nombre, res) in CIELOS.items():
        f = pedir_json(f"https://api.polyhaven.com/files/{pid}")["hdri"][res]["hdr"]
        bajar(f["url"], RAIZ / "cielos" / f"{nombre}.hdr", f.get("md5"))
        creditos.append(f"- Cielo `{nombre}`: [{pid}](https://polyhaven.com/a/{pid})")

    for pid in PROPS:
        g = pedir_json(f"https://api.polyhaven.com/files/{pid}")["gltf"]["1k"]["gltf"]
        carpeta = RAIZ / "props" / pid
        bajar(g["url"], carpeta / f"{pid}.gltf", g.get("md5"))
        for rel, inc in g.get("include", {}).items():
            bajar(inc["url"], carpeta / rel, inc.get("md5"))
        creditos.append(f"- Modelo `{pid}`: [{pid}](https://polyhaven.com/a/{pid})")

    (RAIZ.parent / "CREDITOS.md").write_text(
        "# Créditos\n\nAssets de [Poly Haven](https://polyhaven.com), licencia CC0 (dominio público).\n\n"
        + "\n".join(creditos) + "\n",
        encoding="utf-8",
    )
    print("listo")


if __name__ == "__main__":
    main()
