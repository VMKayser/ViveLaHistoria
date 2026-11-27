"""Fondo de cerros alrededor de Sucre (Churuquella, Sica Sica y la cuenca) para el visor.

Fuente: Terrain Tiles (formato terrarium, z12) de Mapzen/AWS Open Data — uso libre, comercial incluido (ver
recursos/LICENCIAS.md). Los mosaicos crudos están en recursos/originales/terreno_terrarium/ (no versionados).

Salida: web/public/models/fondo/cerros.json — rejilla en metros del LIENZO (x este, y norte) con la altura ya
llevada al cero del lienzo (z del lienzo = altura real − desfase, medido contra reparto/terreno.json). Dentro del
terreno del lienzo (±1 110 m) la rejilla se hunde para no asomar por debajo de la ciudad modelada.

Uso: python3 scripts/fondo_cerros.py
"""

import glob
import json
import math
import os

from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
LAT0, LON0, R, DX, DY = -19.046, -65.2578, 6378137.0, 4.69, 3.09
KX = math.radians(1) * R * math.cos(math.radians(LAT0))
KY = math.radians(1) * R
Z = 12
MEDIO = 12000.0       # medio lado del fondo (m)
PASO = 120.0          # separación de la rejilla (m)
HUECO = 1050.0        # dentro de este cuadrado manda el terreno del lienzo


def a_latlon(x, y):
    return LAT0 + (y - DY) / KY, LON0 + (x - DX) / KX


def tile_xy(lat, lon):
    n = 2 ** Z
    x = (lon + 180) / 360 * n
    la = math.radians(lat)
    y = (1 - math.log(math.tan(la) + 1 / math.cos(la)) / math.pi) / 2 * n
    return x, y


def main():
    tiles = {}
    for f in glob.glob(os.path.join(RAIZ, "recursos", "originales", "terreno_terrarium", "z12_*.png")):
        _, tx, ty = os.path.splitext(os.path.basename(f))[0].split("_")
        tiles[(int(tx), int(ty))] = Image.open(f).convert("RGB").load()

    def elev(lat, lon):
        fx, fy = tile_xy(lat, lon)
        tx, ty = int(fx), int(fy)
        px, py = (fx - tx) * 256, (fy - ty) * 256
        i, j = min(255, int(px)), min(255, int(py))
        t = tiles.get((tx, ty))
        if t is None:
            return None
        r, g, b = t[i, j]
        return r * 256 + g + b / 256 - 32768

    # desfase: altura real − z del lienzo, medido dentro del terreno del lienzo
    ter = json.load(open(os.path.join(RAIZ, "reparto", "terreno.json")))
    ox, oy = ter["origen"]
    dif = []
    for j in range(20, ter["n"] - 20, 25):
        for i in range(20, ter["n"] - 20, 25):
            x, y = ox + i * ter["paso"], oy + j * ter["paso"]
            e = elev(*a_latlon(x, y))
            if e is not None:
                dif.append(e - ter["z"][j][i])
    dif.sort()
    desfase = dif[len(dif) // 2]
    print(f"desfase altura real − lienzo: {desfase:.1f} m ({len(dif)} muestras)")

    n = int(2 * MEDIO / PASO) + 1
    zs = []
    for j in range(n):
        fila = []
        y = -MEDIO + j * PASO
        for i in range(n):
            x = -MEDIO + i * PASO
            e = elev(*a_latlon(x, y))
            z = (e - desfase) if e is not None else 0.0
            # hundir bajo la ciudad (y un margen suave alrededor)
            d = max(abs(x), abs(y))
            if d < HUECO + 300:
                z -= 40.0 * min(1.0, (HUECO + 300 - d) / 300.0)
            fila.append(round(z, 1))
        zs.append(fila)
    sal = os.path.join(RAIZ, "web", "public", "models", "fondo")
    os.makedirs(sal, exist_ok=True)
    with open(os.path.join(sal, "cerros.json"), "w") as fh:
        json.dump({"fuente": "Terrain Tiles (Mapzen/AWS Open Data; SRTM NASA)", "origen": [-MEDIO, -MEDIO],
                   "paso": PASO, "n": n, "z": zs}, fh, separators=(",", ":"))
    print(f"{n}×{n} → web/public/models/fondo/cerros.json")


if __name__ == "__main__":
    main()
