#!/usr/bin/env python3
"""Arreglos de texturas del estilo (Texture2DArray de Godot) a partir de texturas/estilo.json.

Antes cada material de la ciudad tenía su textura de relieve y su atlas de detalle, y eso obligaba a dibujar cada material
aparte (≈20 llamadas por tesela). Con todas las capas en dos arreglos, un solo material dibuja toda la tesela:
  texturas/capas_relieve.png   una capa (512×512) por textura de relieve, apiladas en vertical
  texturas/capas_detalle.png   una capa por celda de cada atlas de detalle (las celdas ya son de 512×512)
  texturas/capas.json          {"relieve": {textura: capa}, "detalle": {atlas: primera capa}}
y los .import para que Godot los importe como Texture2DArray (con mipmaps y la misma compresión que las texturas sueltas).
Uso: python3 ciudad3d/herramientas/capas_textura.py
"""
import json
import os

from PIL import Image

TEX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "texturas")
LADO = 512

IMPORT = """[remap]

importer="2d_array_texture"
type="CompressedTexture2DArray"

[deps]

source_file="res://texturas/{nombre}.png"

[params]

compress/mode=1
compress/high_quality=false
compress/lossy_quality=0.85
compress/hdr_compression=1
compress/channel_pack=1
mipmaps/generate=true
mipmaps/limit=-1
slices/horizontal=1
slices/vertical={capas}
"""


def apilar(nombre, capas):
    hoja = Image.new("L", (LADO, LADO * len(capas)))
    for i, im in enumerate(capas):
        assert im.size == (LADO, LADO), (nombre, i, im.size)
        hoja.paste(im, (0, i * LADO))
    hoja.save(os.path.join(TEX, nombre + ".png"), optimize=True)
    ruta = os.path.join(TEX, nombre + ".png.import")
    texto = IMPORT.format(nombre=nombre, capas=len(capas))
    # si ya existe con los mismos parámetros no se toca (Godot le agrega uid y rutas: reescribirlo los perdería)
    params = texto[texto.index("[params]"):].split()
    if not os.path.exists(ruta) or not set(params) <= set(open(ruta).read().split()):
        open(ruta, "w").write(texto)


def main():
    e = json.load(open(os.path.join(TEX, "estilo.json")))
    relieves = sorted({r[0] for r in e["relieve"].values()})
    apilar("capas_relieve", [Image.open(os.path.join(TEX, n + ".jpg")).convert("L") for n in relieves])
    capas, primera = [], {}
    for atlas, variantes, cols, filas in sorted({(d[0], d[1], d[2], d[3]) for d in e["detalle"].values()}):
        im = Image.open(os.path.join(TEX, f"detalle_{atlas}.jpg")).convert("L")
        w, h = im.size[0] // cols, im.size[1] // filas
        primera[atlas] = len(capas)
        for k in range(variantes):              # celda k: columna k % cols, fila k // cols (fila 0 arriba)
            c, f = k % cols, k // cols
            capas.append(im.crop((c * w, f * h, (c + 1) * w, (f + 1) * h)).resize((LADO, LADO), Image.LANCZOS))
    apilar("capas_detalle", capas)
    json.dump({"relieve": {n: i for i, n in enumerate(relieves)}, "detalle": primera},
              open(os.path.join(TEX, "capas.json"), "w"), indent=1)
    print(f"capas_relieve: {len(relieves)} · capas_detalle: {len(capas)}")


if __name__ == "__main__":
    main()
