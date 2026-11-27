#!/usr/bin/env python3
"""Convierte los HDRI de cielo (Poly Haven, CC0; originales en recursos/originales/cielos/) en JPG listos para el
visor (web/public/cielo/) y escribe cielo.json con la posición del sol/luna en la imagen.

Uso: python3 recursos/cielos_a_web.py
Cada cielo: (archivo HDR, salida, ancho, exposición, calidad JPG). Se reduce con LANCZOS y se guarda en sRGB con curva ACES.
"""
import json, os, subprocess, tempfile
from PIL import Image

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BLENDER = os.path.expanduser("~/apps/blender-5.2.3-linux-x64/blender")
ORIG = os.path.join(RAIZ, "recursos/originales/cielos")
SAL = os.path.join(RAIZ, "web/public/cielo")
CIELOS = [
    ("dia", "kloofendal_38d_partly_cloudy_puresky_4k.hdr", 3072, 1.1, 88),
    ("noche", "qwantani_night_puresky_4k.hdr", 3072, 0.08, 90),
    ("atardecer", "qwantani_dusk_2_puresky.hdr", 2048, 0.5, 90),
]

os.makedirs(SAL, exist_ok=True)
info = {}
for nombre, hdr, ancho, expo, q in CIELOS:
    with tempfile.TemporaryDirectory() as t:
        ppm = os.path.join(t, "c.ppm")
        r = subprocess.run([BLENDER, "-b", "-P", os.path.join(RAIZ, "recursos/hdr_a_ldr_blender.py"), "--",
                            os.path.join(ORIG, hdr), ppm, str(expo)], capture_output=True, text=True)
        sol = [l for l in r.stdout.splitlines() if l.startswith("SOL ")]
        if not sol:
            raise SystemExit(r.stdout[-800:] + r.stderr[-800:])
        info[nombre] = json.loads(sol[0][4:])
        im = Image.open(ppm).convert("RGB")
        if im.width != ancho:
            im = im.resize((ancho, ancho // 2), Image.LANCZOS)
        im.save(os.path.join(SAL, nombre + ".jpg"), quality=q, optimize=True, progressive=True)
        print(nombre, im.size, os.path.getsize(os.path.join(SAL, nombre + ".jpg")) // 1024, "KB", info[nombre])
json.dump(info, open(os.path.join(SAL, "cielo.json"), "w"), indent=1)
