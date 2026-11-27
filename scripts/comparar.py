"""Arma comparaciones lado a lado: render del modelo | foto real.

Uso: python3 scripts/comparar.py <agente> <manzana>
Lee revisiones/<agente>/<manzana>/render_<foto>.jpg y escribe comparacion_<foto>.jpg en la misma carpeta.
"""

import glob
import os
import sys

from PIL import Image, ImageDraw

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def main(agente, mid):
    carpeta = os.path.join(RAIZ, "revisiones", agente, mid)
    n = 0
    for render in sorted(glob.glob(os.path.join(carpeta, "render_*.jpg"))):
        foto = os.path.basename(render)[len("render_"):]
        ruta_foto = os.path.join(RAIZ, "web", "public", "fotos", "medio", foto)
        if not os.path.exists(ruta_foto):
            continue
        a, b = Image.open(render), Image.open(ruta_foto)
        alto = 700
        a = a.resize((int(a.width * alto / a.height), alto))
        b = b.resize((int(b.width * alto / b.height), alto))
        hoja = Image.new("RGB", (a.width + b.width + 10, alto + 30), "white")
        hoja.paste(a, (0, 30))
        hoja.paste(b, (a.width + 10, 30))
        d = ImageDraw.Draw(hoja)
        d.text((8, 8), f"MODELO {mid} ({agente})", fill="black")
        d.text((a.width + 18, 8), f"FOTO REAL {foto}", fill="black")
        hoja.save(os.path.join(carpeta, f"comparacion_{foto}"), quality=85)
        n += 1
    print(f"{n} comparaciones en {carpeta}")


main(*sys.argv[1:3])
