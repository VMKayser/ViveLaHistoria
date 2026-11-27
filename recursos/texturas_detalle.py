#!/usr/bin/env python3
"""Atlas de detalle por rol de material con las texturas elegidas por el usuario en el catálogo (2026-11-23, Poly Haven CC0).

Cada atlas reúne las variantes de un material (cal, zócalo, teja…) en mosaicos de 512 px, en GRISES con media 0,5 y
contraste normalizado: el visor conserva el color de la paleta y solo toma de la textura la forma (hiladas, sillares,
vetas, desconchados). Cada zona de la ciudad usa una variante distinta (estilo.ts elige el mosaico con un ruido lento).

Uso: python3 recursos/texturas_detalle.py → web/public/texturas/detalle_<rol>.jpg + detalle.json
"""
import json
import os

import numpy as np
from PIL import Image, ImageFilter

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ORIG = os.path.join(RAIZ, "recursos/originales/catalogo/polyhaven/texturas")
SAL = os.path.join(RAIZ, "web/public/texturas")
T = 512

# rol del visor: (grupo del catálogo, texturas elegidas, metros por repetición, fuerza)
ROLES = {
    "muro": ("cal", ["plastered_wall", "plastered_wall_02", "plastered_wall_04", "painted_plaster_wall", "patterned_plaster_wall",
                     "damaged_plaster", "rough_plaster_broken"], 2.5, 0.16),
    "zocalo_piedra": ("zocalo", ["large_sandstone_blocks", "medieval_blocks_02", "castle_brick_02_white", "plaster_stone_wall_01",
                                 "rustic_stone_wall"], 2.0, 0.45),
    "teja": ("teja", ["clay_roof_tiles_02", "ceramic_roof_01"], 1.6, 0.55),
    "adoquin": ("adoquin", ["square_cobblestone"], 1.6, 0.55),
    "vereda": ("vereda", ["precast_stone_paving", "rectangular_paving"], 2.0, 0.4),
    "madera": ("madera", ["weathered_brown_planks", "old_planks_02"], 1.4, 0.45),
    "hierro": ("hierro", ["rusty_painted_metal", "rusty_metal_02", "metal_plate"], 1.0, 0.3),
}


def mosaico(ruta):
    im = Image.open(ruta).convert("L").resize((T, T), Image.LANCZOS)
    a = np.asarray(im, dtype=np.float32) / 255
    # quita el sombreado de baja frecuencia (la luz la pone el visor) y normaliza el contraste
    bajo = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40)), dtype=np.float32) / 255
    d = a - bajo
    d = d / (d.std() * 4 + 1e-4)
    return np.clip(0.5 + d, 0, 1)


def main():
    meta = {}
    for rol, (grupo, nombres, escala, fuerza) in ROLES.items():
        tiles = [mosaico(os.path.join(ORIG, grupo, n + ".jpg")) for n in nombres]
        cols = min(4, len(tiles))
        filas = (len(tiles) + cols - 1) // cols
        atlas = np.full((filas * T, cols * T), 0.5, dtype=np.float32)
        for k, t in enumerate(tiles):
            r, c = divmod(k, cols)
            atlas[r * T:(r + 1) * T, c * T:(c + 1) * T] = t
        Image.fromarray((atlas * 255).astype(np.uint8)).save(os.path.join(SAL, f"detalle_{rol}.jpg"), quality=86)
        meta[rol] = dict(url=f"/texturas/detalle_{rol}.jpg", n=len(tiles), cols=cols, filas=filas, escala=escala, fuerza=fuerza,
                         fuentes=nombres)
        print(rol, len(tiles), f"{cols}x{filas}")
    json.dump(meta, open(os.path.join(SAL, "detalle.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
