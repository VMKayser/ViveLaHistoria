#!/usr/bin/env python3
"""Descarga los recursos gráficos libres del juego y registra su origen y licencia.

Fuentes:
- Poly Haven (https://polyhaven.com): texturas PBR, modelos 3D y cielos HDRI, licencia CC0.
- Wikimedia Commons: retrato de Bolívar de José Gil de Castro, dominio público.

Uso (desde la raíz del repositorio):
    python3 herramientas/descargar_assets.py

Deja todo en juego/assets/ y escribe juego/assets/LICENCIAS.md.
Es idempotente: no vuelve a descargar archivos que ya existen.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "juego" / "assets"
AGENTE = "ViveLaHistoria-hackathon/1.0"

# id de Poly Haven -> (resolución, uso en el juego)
TEXTURAS = {
    "white_stucco": ("2k", "Muros encalados de la sala y el patio"),
    "cobblestone_floor_04": ("2k", "Empedrado del patio"),
    "square_brick_floor": ("2k", "Piso de baldosa de la Sala Mayor"),
    "dark_wooden_planks": ("1k", "Tablas del techo (artesonado)"),
    "rough_wood": ("1k", "Vigas del techo y barandas"),
    "wood_table_worn": ("1k", "Madera de muebles y coro"),
    "large_sandstone_blocks_01": ("1k", "Piedra de columnas, pileta y escalones"),
    "clay_roof_tiles": ("1k", "Teja colonial del alero de la galería"),
}

MODELOS = {
    "gallinera_chair": "Sillas talladas de los diputados",
    "WoodenChair_01": "Sillón del presidente de la Asamblea",
    "WoodenTable_01": "Mesa de la Secretaría",
    "brass_candleholders": "Candelabros sobre la mesa de la presidencia",
    "Chandelier_03": "Arañas de velas de la Sala Mayor",
    "large_castle_door": "Puerta de madera de la Sala Mayor",
    "wooden_lantern_01": "Faroles del patio",
    "planter_pot_clay": "Macetas de barro del patio",
    "potted_plant_02": "Plantas del patio",
}

HDRI = ("kloofendal_48d_partly_cloudy_puresky", "2k", "Cielo de la escena")

RETRATO = {
    "archivo": "arte/bolivar_gil_de_castro.jpg",
    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/40/"
           "Jos%C3%A9_Gil_de_Castro_-_Sim%C3%B3n_Bol%C3%ADvar_-_Google_Art_Project.jpg/"
           "1280px-Jos%C3%A9_Gil_de_Castro_-_Sim%C3%B3n_Bol%C3%ADvar_-_Google_Art_Project.jpg",
    "pagina": "https://commons.wikimedia.org/wiki/File:Jos%C3%A9_Gil_de_Castro_-_Sim%C3%B3n_Bol%C3%ADvar_-_Google_Art_Project.jpg",
}


def descargar(url: str, destino: Path) -> None:
    """Descarga con curl: reintenta y reanuda si la conexión se corta."""
    if destino.exists() and destino.stat().st_size > 0:
        return
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_name(destino.name + ".parcial")
    comando = ["curl", "-sSfL", "--retry", "8", "--retry-all-errors", "--retry-delay", "3",
               "--connect-timeout", "30", "--speed-limit", "20000", "--speed-time", "15", "-C", "-", "-A", AGENTE, "-o", str(parcial), url]
    for _ in range(6):
        if subprocess.run(comando).returncode == 0:
            parcial.rename(destino)
            print(f"  {destino.relative_to(RAIZ)}")
            return
    sys.exit(f"No se pudo descargar {url}")


def archivos_polyhaven(asset_id: str) -> dict:
    for intento in range(5):
        try:
            pedido = urllib.request.Request(f"https://api.polyhaven.com/files/{asset_id}", headers={"User-Agent": AGENTE})
            with urllib.request.urlopen(pedido, timeout=60) as respuesta:
                return json.load(respuesta)
        except OSError as error:
            print(f"  reintento {intento + 1} para {asset_id}: {error}")
            time.sleep(3)
    sys.exit(f"No se pudo consultar Poly Haven para {asset_id}")


def bajar_textura(asset_id: str, resolucion: str) -> None:
    archivos = archivos_polyhaven(asset_id)
    mapas = {"Diffuse": "albedo", "nor_gl": "normal", "arm": "arm"}
    for mapa, nombre in mapas.items():
        if mapa not in archivos:
            sys.exit(f"La textura {asset_id} no tiene el mapa {mapa}")
        url = archivos[mapa][resolucion]["jpg"]["url"]
        descargar(url, ASSETS / "texturas" / asset_id / f"{nombre}.jpg")


def bajar_modelo(asset_id: str) -> None:
    gltf = archivos_polyhaven(asset_id)["gltf"]["1k"]["gltf"]
    carpeta = ASSETS / "modelos" / asset_id
    descargar(gltf["url"], carpeta / f"{asset_id}.gltf")
    for ruta_relativa, datos in gltf.get("include", {}).items():
        descargar(datos["url"], carpeta / ruta_relativa)


def escribir_licencias() -> None:
    filas_texturas = "\n".join(
        f"| `texturas/{i}/` | {uso} | [Poly Haven](https://polyhaven.com/a/{i}) | CC0 |"
        for i, (_, uso) in TEXTURAS.items())
    filas_modelos = "\n".join(
        f"| `modelos/{i}/` | {uso} | [Poly Haven](https://polyhaven.com/a/{i}) | CC0 |"
        for i, uso in MODELOS.items())
    texto = f"""# Licencias de los recursos gráficos

Generado por `herramientas/descargar_assets.py`. Todo lo listado aquí se puede usar,
modificar y redistribuir, incluso con fines comerciales.

| Archivo | Uso en el juego | Origen | Licencia |
| --- | --- | --- | --- |
{filas_texturas}
{filas_modelos}
| `cielo/{HDRI[0]}.hdr` | {HDRI[2]} | [Poly Haven](https://polyhaven.com/a/{HDRI[0]}) | CC0 |
| `{RETRATO['archivo']}` | Retrato de Bolívar en el Salón de la Independencia | [Wikimedia Commons]({RETRATO['pagina']}) | Dominio público |

Nota sobre el retrato: es una de las versiones que José Gil de Castro pintó de Bolívar
(ca. 1823, según Wikimedia Commons). El ejemplar que se exhibe en la Casa de la Libertad
puede ser otra versión; el juego lo usa como referencia visual, no como reproducción exacta.

Los modelos 3D propios del equipo (Blender) se agregan a esta tabla con su autor y licencia.
"""
    (ASSETS / "LICENCIAS.md").write_text(texto, encoding="utf-8")


def main() -> None:
    print("Texturas")
    for asset_id, (resolucion, _) in TEXTURAS.items():
        bajar_textura(asset_id, resolucion)
    print("Modelos")
    for asset_id in MODELOS:
        bajar_modelo(asset_id)
    print("Cielo")
    hdri_id, resolucion, _ = HDRI
    url = archivos_polyhaven(hdri_id)["hdri"][resolucion]["hdr"]["url"]
    descargar(url, ASSETS / "cielo" / f"{hdri_id}.hdr")
    print("Retrato")
    descargar(RETRATO["url"], ASSETS / RETRATO["archivo"])
    escribir_licencias()
    print("Listo: juego/assets/LICENCIAS.md")


if __name__ == "__main__":
    main()
