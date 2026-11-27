#!/usr/bin/env python3
"""Textura de racimos de hojas para las copas de los árboles (texturas/hojas.png), dibujada aquí (sin recursos de terceros).

Atlas de 2×2 celdas de 256 px: cada celda es un racimo de hojas ovaladas y puntiagudas que salen del centro, con nervadura,
borde algo más oscuro y un tono distinto por hoja. RGB en grises (el color lo pone el árbol: vértices y shader), A = forma.
Se dibuja a 4× y se reduce (bordes suaves: el recorte por alfa queda limpio también en los mipmaps).
Uso: python3 ciudad3d/herramientas/hojas_textura.py
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "texturas")
CELDA = 256
SS = 4
IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[deps]

source_file="res://texturas/hojas.png"

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.75
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=true
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=0
"""


def hoja(draw, cx, cy, ang, largo, ancho, tono):
    """Una hoja: contorno ovalado con punta, nervadura central más clara y mitad de sombra."""
    pts = []
    for k in range(25):
        t = k / 24
        r = math.sin(math.pi * t) ** 0.8 * (1 - 0.35 * t)        # más ancha cerca del pecíolo, punta aguda
        pts.append((t * largo, r * ancho))
    contorno = pts + [(x, -y) for x, y in reversed(pts)]
    ca, sa = math.cos(ang), math.sin(ang)

    def a_pantalla(p):
        return (cx + p[0] * ca - p[1] * sa, cy + p[0] * sa + p[1] * ca)

    borde = int(255 * tono * 0.72)
    draw.polygon([a_pantalla(p) for p in contorno], fill=(borde, 255))
    interior = [(x * 0.96 + largo * 0.02, y * 0.8) for x, y in contorno]
    draw.polygon([a_pantalla(p) for p in interior], fill=(int(255 * tono), 255))
    # media hoja en sombra (la hoja no es plana)
    mitad = [(x * 0.96 + largo * 0.02, max(y, 0) * 0.8) for x, y in contorno]
    draw.polygon([a_pantalla(p) for p in mitad], fill=(int(255 * tono * 0.86), 255))
    draw.line([a_pantalla((largo * 0.02, 0)), a_pantalla((largo * 0.9, 0))], fill=(min(255, int(255 * tono * 1.12)), 255),
              width=max(1, int(largo * 0.035)))


def racimo(semilla):
    rng = np.random.default_rng(semilla)
    n = CELDA * SS
    img = Image.new("LA", (n, n), (0, 0))
    d = ImageDraw.Draw(img)
    c = n / 2
    hojas = []
    for _ in range(int(rng.integers(60, 75))):
        # posición: disco algo irregular, más denso en el centro; la hoja apunta hacia afuera
        r = (rng.random() ** 0.6) * n * 0.36
        a = rng.random() * math.tau
        x, y = c + r * math.cos(a), c + r * math.sin(a)
        ang = a + rng.normal(0, 0.5)
        largo = n * rng.uniform(0.11, 0.17)
        hojas.append((r, x, y, ang, largo, largo * rng.uniform(0.28, 0.38), rng.uniform(0.55, 1.0)))
    hojas.sort(key=lambda h: -h[0])           # primero las de afuera: las del centro quedan encima
    for r, x, y, ang, largo, ancho, tono in hojas:
        # las de afuera, algo más claras (les da el sol); las de adentro, más oscuras
        hoja(d, x - largo * 0.15 * math.cos(ang), y - largo * 0.15 * math.sin(ang), ang, largo, ancho,
             tono * (0.75 + 0.25 * r / (n * 0.36)))
    img = img.filter(ImageFilter.GaussianBlur(SS * 0.35)).resize((CELDA, CELDA), Image.LANCZOS)
    la = np.asarray(img, np.float32) / 255
    # gris ya multiplicado por la cobertura en el borde → se reconstruye el tono y se endurece un poco el alfa
    a = np.clip((la[..., 1] - 0.15) / 0.7, 0, 1)
    g = np.clip(la[..., 0] / np.maximum(la[..., 1], 1e-3), 0, 1)
    return np.dstack([g, g, g, a])


def main():
    atlas = np.zeros((CELDA * 2, CELDA * 2, 4), np.float32)
    for k in range(4):
        fx, fy = k % 2, k // 2
        atlas[fy * CELDA:(fy + 1) * CELDA, fx * CELDA:(fx + 1) * CELDA] = racimo(97 + k * 13)
    ruta = os.path.join(TEX, "hojas.png")
    Image.fromarray((np.clip(atlas, 0, 1) * 255).astype(np.uint8), "RGBA").save(ruta, optimize=True)
    if not os.path.exists(ruta + ".import"):
        open(ruta + ".import", "w").write(IMPORT)
    print(ruta)


if __name__ == "__main__":
    main()
