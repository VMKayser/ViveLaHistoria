"""Indexa las fotos de fotos/ para la herramienta del mapa (web/src/app/mapa).

- Lee fecha y GPS del EXIF.
- Genera miniaturas (web/public/fotos/mini) y versión media (web/public/fotos/medio), ya rotadas.
- Escribe web/public/fotos/indice.json.

Es incremental: las miniaturas existentes no se regeneran. Uso: cd web && npm run fotos
"""

import json
import os
import sys

from PIL import Image, ImageOps

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "blender", "scripts"))
from geo import a_metros  # noqa: E402

FOTOS = os.path.join(RAIZ, "fotos")
PUB = os.path.join(RAIZ, "web", "public", "fotos")
TAMANOS = {"mini": 360, "medio": 1600}
EXT = (".jpg", ".jpeg", ".png", ".heic", ".webp")


def grados(v, ref):
    g = float(v[0]) + float(v[1]) / 60 + float(v[2]) / 3600
    return -g if ref in ("S", "W") else g


def gps(exif):
    g = exif.get_ifd(0x8825)
    if not g or 2 not in g or 4 not in g:
        return None
    lat, lon = grados(g[2], g.get(1, "N")), grados(g[4], g.get(3, "E"))
    if lat == 0 and lon == 0:
        return None
    metodo = g.get(27, b"")
    metodo = metodo.decode("ascii", "ignore").replace("ASCII", "").strip("\x00 ") if isinstance(metodo, bytes) else str(metodo)
    x, y = a_metros(lat, lon)
    return {"lat": round(lat, 7), "lon": round(lon, 7), "x": round(x, 1), "y": round(y, 1), "metodo": metodo}


def main():
    for t in TAMANOS:
        os.makedirs(os.path.join(PUB, t), exist_ok=True)
    indice = []
    for nombre in sorted(os.listdir(FOTOS)):
        if not nombre.lower().endswith(EXT):
            continue
        ruta = os.path.join(FOTOS, nombre)
        try:
            im = Image.open(ruta)
        except Exception as e:  # formato no soportado (p. ej. HEIC sin plugin)
            print("omitida", nombre, e)
            continue
        exif = im.getexif()
        fecha = exif.get_ifd(0x8769).get(36867) or exif.get(306) or ""
        salida = os.path.splitext(nombre)[0] + ".jpg"
        rotada = None
        for t, lado in TAMANOS.items():
            destino = os.path.join(PUB, t, salida)
            if os.path.exists(destino):
                continue
            if rotada is None:
                rotada = ImageOps.exif_transpose(im).convert("RGB")
            copia = rotada.copy()
            copia.thumbnail((lado, lado))
            copia.save(destino, quality=82)
        indice.append({
            "archivo": nombre,
            "web": salida,
            "fecha": fecha.replace(":", "-", 2),
            "gps": gps(exif),
        })
    with open(os.path.join(PUB, "indice.json"), "w") as fh:
        json.dump(indice, fh, ensure_ascii=False, indent=1)
    print(f"{len(indice)} fotos indexadas")


main()
