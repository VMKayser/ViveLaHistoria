#!/usr/bin/env python3
"""Ajusta la importación de texturas de juego/assets para la exportación web.

- Compresión de GPU (VRAM): S3TC en navegadores de escritorio, mucho menos memoria y descarga.
- Mapas de normales marcados como tales (compresión BC5/RGTC, sin artefactos de color).
- Mipmaps: sin ellos las baldosas y el empedrado parpadean a la distancia.
- Límite de 1024 px para texturas que se repiten (la proyección triplanar las repite cada 1-2 m)
  y de 512 px para los muebles.
- Luz horneada en BC7 (alta calidad) y sin mipmaps, para evitar bandas y sangrado entre islas.

Uso: python3 herramientas/optimizar_importacion.py && godot --headless --path juego --import
"""

from __future__ import annotations

import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "juego" / "assets"
EXTENSIONES = {".jpg", ".jpeg", ".png", ".hdr", ".exr", ".webp"}


def parametros(archivo: Path) -> dict[str, str]:
    nombre = archivo.name.lower()
    base = {
        "compress/mode": "2",
        "compress/high_quality": "false",
        "mipmaps/generate": "true",
        "process/size_limit": "1024",
        "compress/normal_map": "0",
    }
    if "normal" in nombre or "_nor_" in nombre:
        base["compress/normal_map"] = "1"
    if "modelos" in archivo.parts:  # muebles: ocupan poco en pantalla
        base["process/size_limit"] = "512"
    if archivo.suffix in {".hdr", ".exr"}:
        base.update({"compress/high_quality": "true", "process/size_limit": "2048"})
    if archivo.parent.name == "arquitectura":  # luz horneada
        base.update({"compress/high_quality": "true", "mipmaps/generate": "false", "process/size_limit": "0"})
    return base


def ajustar(importacion: Path, valores: dict[str, str]) -> bool:
    texto = importacion.read_text(encoding="utf-8")
    if 'importer="texture"' not in texto:
        return False
    original = texto
    for clave, valor in valores.items():
        patron = re.compile(rf"^{re.escape(clave)}=.*$", re.MULTILINE)
        if patron.search(texto):
            texto = patron.sub(f"{clave}={valor}", texto)
        else:
            texto = texto.replace("[params]\n", f"[params]\n\n{clave}={valor}\n", 1)
    if texto != original:
        importacion.write_text(texto, encoding="utf-8")
        return True
    return False


def main() -> None:
    cambiados = 0
    for archivo in sorted(ASSETS.rglob("*")):
        if archivo.suffix.lower() not in EXTENSIONES:
            continue
        importacion = archivo.with_name(archivo.name + ".import")
        if importacion.exists() and ajustar(importacion, parametros(archivo)):
            cambiados += 1
    print(f"Importación ajustada en {cambiados} texturas. Ahora: godot --headless --path juego --import")


if __name__ == "__main__":
    main()
