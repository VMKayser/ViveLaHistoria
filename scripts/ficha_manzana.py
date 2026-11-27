"""Ficha de trabajo de una manzana: plano con edificios, lados y fotos + hoja con las fotos.

Uso: python3 scripts/ficha_manzana.py M021
Salidas en revisiones/<dueño>/<manzana>/:
  ficha.md          edificios (id, medidas, lados que dan a la calle) y fotos con su edificio
  ficha_plano.png   plano: edificios de la manzana (con id y número de lado), vecinos, calles y puntos de fotos numerados
  ficha_fotos.jpg   hoja con todas las fotos numeradas igual que en el plano
"""

import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "blender", "kit"))
import datos  # noqa: E402  (kit/datos.py no depende de Blender)


def fuente(n):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", n)
    except OSError:
        return ImageFont.load_default()


def main(mid):
    m = datos.manzana(mid)
    carpeta = os.path.join(RAIZ, "revisiones", m["dueno"], mid)
    os.makedirs(carpeta, exist_ok=True)
    ub = datos.ubicaciones()

    # fotos de la manzana + fotos de espacio público a menos de 15 m
    fotos = list(m["fotos"])
    for s in datos.reparto()["fotos_espacio_publico"]:
        if any(min(math.hypot(s["x"] - x, s["y"] - y) for x, y in e["huella"]) < 15 for e in m["edificios"]):
            fotos.append(s["archivo"])
    num = {f: k + 1 for k, f in enumerate(fotos)}

    lineas = [f"# Ficha {mid} (dueño: {m['dueno']})", "",
              f"Centro {m['centro']}, {len(m['edificios'])} edificios, {m.get('area_m2', '-')} m².", "",
              "Coordenadas en metros del lienzo (X este, Y norte). Lados en orden antihorario; "
              "'a calle' = fachada visible desde la calle (revisar con las fotos; se puede forzar con lados_calle).", ""]
    todos_lados = {}
    for e in m["edificios"]:
        ls = datos.lados(e["huella"])
        todos_lados[e["id"]] = ls
        suelo = [datos.altura_suelo(x, y) for x, y in e["huella"]]
        lineas.append(f"## {e['id']} {('— ' + e['nombre']) if e['nombre'] else ''}")
        lineas.append(f"- área {e['area_m2']} m², altura en el lienzo {e['altura_lienzo']} m (genérica, NO confiable), "
                      f"suelo entre {min(suelo):.1f} y {max(suelo):.1f} m (desnivel {max(suelo) - min(suelo):.1f} m)")
        for l in ls:
            if l["largo"] >= 1.5:
                lineas.append(f"- lado {l['i']}: {l['largo']} m{' — A CALLE ' + l['calle'] if l['a_calle'] else ''}")
        if e["fotos"]:
            lineas.append("- fotos: " + ", ".join(f"#{num[f]} {f}" for f in e["fotos"]))
        lineas.append("")
    extra = [f for f in fotos if f not in m["fotos"]]
    if extra:
        lineas.append("## Fotos de calle/plaza cercanas (contexto)")
        lineas += [f"- #{num[f]} {f} ({ub[f]['calle']})" for f in extra]
    with open(os.path.join(carpeta, "ficha.md"), "w") as fh:
        fh.write("\n".join(lineas) + "\n")

    plano(m, todos_lados, fotos, num, ub, os.path.join(carpeta, "ficha_plano.png"))
    hoja(fotos, num, os.path.join(carpeta, "ficha_fotos.jpg"))
    print("\n".join(lineas))
    print(f"\nArchivos en {carpeta}")


def plano(m, todos_lados, fotos, num, ub, ruta):
    pts = [p for e in m["edificios"] for p in e["huella"]] + [(ub[f]["x"], ub[f]["y"]) for f in fotos] + m.get("poligono", [])
    if not pts:  # BASE: toda la zona de trabajo
        z = datos.reparto()["zona"]
        pts = [(z["xmin"] + 25, z["ymin"] + 25), (z["xmax"] - 25, z["ymax"] - 25)]
    xmin, xmax = min(p[0] for p in pts) - 25, max(p[0] for p in pts) + 25
    ymin, ymax = min(p[1] for p in pts) - 25, max(p[1] for p in pts) + 25
    esc = min(1100 / (xmax - xmin), 1100 / (ymax - ymin))
    W, H = int((xmax - xmin) * esc), int((ymax - ymin) * esc)
    img = Image.new("RGB", (W, H), "#f4f1ea")
    d = ImageDraw.Draw(img)

    def px(x, y):
        return ((x - xmin) * esc, (ymax - y) * esc)

    for c in datos.calles():
        if any(xmin <= x <= xmax and ymin <= y <= ymax for x, y, _ in c["puntos"]):
            d.line([px(x, y) for x, y, _ in c["puntos"]], fill="#d6cdbb", width=max(2, int(5 * esc)))
    for mm in datos.reparto()["manzanas"]:
        if mm["id"] == m["id"]:
            continue
        for e in mm["edificios"]:
            if any(xmin <= x <= xmax and ymin <= y <= ymax for x, y in e["huella"]):
                d.polygon([px(*p) for p in e["huella"]], fill="#e2ddd4", outline="#b9b2a6")
    f12, f10 = fuente(13), fuente(11)
    if m.get("poligono"):
        d.polygon([px(*p) for p in m["poligono"]], fill="#cfe3b0", outline="#4d6b2a")
    for e in m["edificios"]:
        d.polygon([px(*p) for p in e["huella"]], fill="#f2b48a", outline="#8a3d12")
        for l in todos_lados[e["id"]]:
            if l["largo"] < 1.5:
                continue
            ax, ay = px(*l["a"])
            bx, by = px(*l["b"])
            if l["a_calle"]:
                d.line([(ax, ay), (bx, by)], fill="#c0392b", width=4)
            cx, cy = px((l["a"][0] + l["b"][0]) / 2 - l["normal"][0] * 1.5, (l["a"][1] + l["b"][1]) / 2 - l["normal"][1] * 1.5)
            d.text((cx, cy), str(l["i"]), fill="#5a2a0c", font=f10, anchor="mm")
        d.text(px(*e["centro"]), e["id"], fill="black", font=f12, anchor="mm")
    for f in fotos:
        x, y = px(ub[f]["x"], ub[f]["y"])
        d.ellipse([x - 9, y - 9, x + 9, y + 9], fill="#1f4e79", outline="white")
        d.text((x, y), str(num[f]), fill="white", font=f10, anchor="mm")
    # flecha de norte y escala
    d.text((W - 30, 15), "N↑", fill="black", font=f12)
    d.line([(15, H - 15), (15 + 10 * esc, H - 15)], fill="black", width=3)
    d.text((15, H - 32), "10 m", fill="black", font=f10)
    d.text((15, 10), f"{m['id']} · rojo = lado a calle · números chicos = índice de lado · círculos azules = fotos", fill="black", font=f10)
    img.save(ruta)


def hoja(fotos, num, ruta, ancho=420, cols=4):
    if not fotos:
        return
    ims = []
    for f in fotos:
        im = Image.open(datos.ruta_foto(f, "mini"))
        im = im.resize((ancho, int(ancho * im.height / im.width)))
        ims.append((f, im))
    alto = max(im.height for _, im in ims) + 24
    filas = math.ceil(len(ims) / cols)
    out = Image.new("RGB", (cols * ancho, filas * alto), "white")
    d = ImageDraw.Draw(out)
    for k, (f, im) in enumerate(ims):
        x, y = (k % cols) * ancho, (k // cols) * alto
        out.paste(im, (x, y + 24))
        d.text((x + 4, y + 4), f"#{num[f]} {f}", fill="black", font=fuente(13))
    out.save(ruta, quality=85)


main(sys.argv[1])
