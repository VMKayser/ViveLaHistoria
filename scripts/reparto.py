"""Divide el centro histórico en manzanas y las reparte entre los agentes (claude / codex).

Salidas (en reparto/):
  manzanas.json  una entrada por manzana: id, dueño, edificios (huella en metros, pisos), fotos asociadas
  reparto.png    mapa visual del reparto

Uso: python3 scripts/reparto.py
Las coordenadas son las del lienzo (metros, X este, Y norte); ver blender/scripts/geo.py.
"""

import hashlib
import json
import lzma
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(RAIZ, "blender", "scripts"))
from geo import a_metros  # noqa: E402

SALIDA = os.path.join(RAIZ, "reparto")

# Zona de trabajo: rectángulo que cubre las fotos del 2026-11-05 con margen de ~1 manzana
ZONA = (-350.0, -410.0, -50.0, 110.0)  # xmin, ymin, xmax, ymax

# Frontera del reparto: la Calle José Álvarez de Arenales (fila de San Miguel).
# Las manzanas con centro al NORTE de la recta -> claude; al SUR -> codex.
# La recta se define por dos puntos de la calle (se calcula en main a partir de OSM).
CALLE_FRONTERA = "Calle José Álvarez de Arenales"


def anillo(geom):
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"][0][0]
    if geom["type"] == "Polygon":
        return geom["coordinates"][0]
    if geom["type"] == "LineString" and geom["coordinates"][0] == geom["coordinates"][-1]:
        return geom["coordinates"]
    return None


def area_centro(pts):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        c = x0 * y1 - x1 * y0
        a += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a) < 1e-9:
        return 0.0, sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    return abs(a) / 2, cx / (3 * a), cy / (3 * a)


def dist_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy or 1
    u = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / l2))
    return math.hypot(px - a[0] - u * dx, py - a[1] - u * dy)


def dentro(px, py, pts):
    r = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
            r = not r
    return r


def dist_poly(px, py, pts):
    if dentro(px, py, pts):
        return 0.0
    return min(dist_seg(px, py, a, b) for a, b in zip(pts, pts[1:] + pts[:1]))


def main():
    os.makedirs(SALIDA, exist_ok=True)
    datos = json.load(lzma.open(os.path.join(RAIZ, "Sucre.osm.geojson.xz")))
    xmin, ymin, xmax, ymax = ZONA

    # Edificios: huellas del lienzo FBX (OSM tiene pocos edificios mapeados en el centro).
    # Generar antes con blender/scripts/extraer_huellas.py
    edificios = []
    for e in json.load(open(os.path.join(SALIDA, "edificios_lienzo.json"))):
        pts = [tuple(p) for p in e["huella"]]
        area, cx, cy = area_centro(pts)
        if not (xmin <= cx <= xmax and ymin <= cy <= ymax) or area < 4:
            continue
        edificios.append({
            "id": "E" + hashlib.md5(f"{cx:.1f},{cy:.1f}".encode()).hexdigest()[:6],
            "nombre": "",
            "clase_lienzo": e["clase"],
            "altura_lienzo": e["altura"],
            "base_z": e["base_z"],
            "area_m2": round(area, 1),
            "centro": [round(cx, 1), round(cy, 1)],
            "huella": [list(p) for p in pts],
        })

    calles = []
    lugares = []
    for f in datos["features"]:
        p, g = f["properties"], f["geometry"]
        if p.get("highway") and g["type"] == "LineString":
            pts = [a_metros(lat, lon) for lon, lat in g["coordinates"]]
            if any(xmin - 80 <= x <= xmax + 80 and ymin - 80 <= y <= ymax + 80 for x, y in pts):
                calles.append({"nombre": p.get("name", ""), "tipo": p["highway"], "pts": pts})
        elif p.get("name") and "highway" not in p and g["type"] in ("Point", "MultiPolygon"):
            if g["type"] == "Point":
                lon, lat = g["coordinates"]
            else:
                r = g["coordinates"][0][0]
                lon, lat = sum(c[0] for c in r) / len(r), sum(c[1] for c in r) / len(r)
            x, y = a_metros(lat, lon)
            if xmin <= x <= xmax and ymin <= y <= ymax and not str(p.get("place", "")).startswith(("city", "town")):
                lugares.append((p["name"], x, y))
    # nombre OSM de los edificios: lugares con nombre que caen dentro de la huella
    for e in edificios:
        dentro_ = [n for n, x, y in lugares if dentro(x, y, [tuple(q) for q in e["huella"]])]
        e["nombre"] = " / ".join(dict.fromkeys(dentro_))

    # Manzanas: edificios que se tocan (muros compartidos, < 1.5 m) forman la misma manzana
    n = len(edificios)
    padre = list(range(n))

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    cajas = []
    for e in edificios:
        xs = [p[0] for p in e["huella"]]
        ys = [p[1] for p in e["huella"]]
        cajas.append((min(xs), min(ys), max(xs), max(ys)))
    for i in range(n):
        for j in range(i + 1, n):
            a, b = cajas[i], cajas[j]
            if a[0] > b[2] + 1.5 or b[0] > a[2] + 1.5 or a[1] > b[3] + 1.5 or b[1] > a[3] + 1.5:
                continue
            hi, hj = edificios[i]["huella"], edificios[j]["huella"]
            if any(dist_poly(x, y, hj) < 1.5 for x, y in hi) or any(dist_poly(x, y, hi) < 1.5 for x, y in hj):
                padre[raiz(i)] = raiz(j)

    grupos = {}
    for i in range(n):
        grupos.setdefault(raiz(i), []).append(edificios[i])

    # Recta de la frontera: ajuste por mínimos cuadrados a los puntos de la calle frontera dentro de la zona
    fpts = [p for c in calles if c["nombre"] == CALLE_FRONTERA for p in c["pts"] if xmin - 50 <= p[0] <= xmax + 50]
    mx = sum(p[0] for p in fpts) / len(fpts)
    my = sum(p[1] for p in fpts) / len(fpts)
    sxx = sum((p[0] - mx) ** 2 for p in fpts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in fpts)
    pend = sxy / sxx

    def lado_norte(x, y):
        return y > my + pend * (x - mx)

    fotos = json.load(open(os.path.join(RAIZ, "fotos", "ubicaciones.json")))["fotos"]

    manzanas = []
    for edifs in grupos.values():
        area = sum(e["area_m2"] for e in edifs)
        cx = sum(e["centro"][0] * e["area_m2"] for e in edifs) / area
        cy = sum(e["centro"][1] * e["area_m2"] for e in edifs) / area
        manzanas.append({"centro": [round(cx, 1), round(cy, 1)], "area_m2": round(area, 1), "edificios": edifs})

    # ids estables de norte a sur, oeste a este
    manzanas.sort(key=lambda m: (-round(m["centro"][1] / 40), m["centro"][0]))
    for k, m in enumerate(manzanas, 1):
        m["id"] = f"M{k:03d}"
        m["dueno"] = "claude" if lado_norte(*m["centro"]) else "codex"
        # foto -> edificio más cercano (a menos de 12 m): el punto marca dónde está lo fotografiado
        m["fotos"] = []
        for e in m["edificios"]:
            e["fotos"] = []
    todos = [(m, e) for m in manzanas for e in m["edificios"]]
    sin_edificio = []
    for archivo, u in sorted(fotos.items()):
        mejor = min(todos, key=lambda me: dist_poly(u["x"], u["y"], me[1]["huella"]))
        d = dist_poly(u["x"], u["y"], mejor[1]["huella"])
        if d <= 12:
            mejor[1]["fotos"].append(archivo)
            mejor[0]["fotos"].append(archivo)
        else:
            sin_edificio.append({"archivo": archivo, "x": u["x"], "y": u["y"], "calle": u["calle"], "cerca": u["cerca"]})

    # las fotos de plaza/calle (sin edificio a 12 m) van al dueño del lado donde caen
    for s in sin_edificio:
        s["dueno"] = "claude" if lado_norte(s["x"], s["y"]) else "codex"

    resumen = {}
    for m in manzanas:
        r = resumen.setdefault(m["dueno"], {"manzanas": 0, "edificios": 0, "fotos": 0, "area_m2": 0})
        r["manzanas"] += 1
        r["edificios"] += len(m["edificios"])
        r["fotos"] += len(m["fotos"])
        r["area_m2"] += m["area_m2"]
    for s in sin_edificio:
        resumen[s["dueno"]]["fotos_espacio_publico"] = resumen[s["dueno"]].get("fotos_espacio_publico", 0) + 1

    # Espacios públicos con dueño propio (además de las manzanas)
    plaza = None
    for f in datos["features"]:
        p = f["properties"]
        if p.get("name") == "Plaza 25 de Mayo" and p.get("leisure") == "park" and f["geometry"]["type"] == "MultiPolygon":
            plaza = [list(map(lambda v: round(v, 2), a_metros(lat, lon))) for lon, lat in f["geometry"]["coordinates"][0][0]]
    espacios = []
    if plaza:
        _, px_, py_ = area_centro([tuple(q) for q in plaza])
        f_plaza = [s["archivo"] for s in sin_edificio if s["calle"] == "Plaza 25 de Mayo" or dentro(s["x"], s["y"], [tuple(q) for q in plaza])]
        espacios.append({"id": "P01", "nombre": "Plaza 25 de Mayo (interior: jardines, fuente/monumento, árboles, bancos, faroles, caminos)",
                         "dueno": "codex", "centro": [round(px_, 1), round(py_, 1)], "poligono": plaza,
                         "edificios": [], "fotos": f_plaza})
    espacios.append({"id": "BASE", "nombre": "Base urbana de toda la zona: terreno, calzadas, veredas, bordillos y plazas sin dueño",
                     "dueno": "claude", "centro": [round((xmin + xmax) / 2, 1), round((ymin + ymax) / 2, 1)],
                     "edificios": [], "fotos": []})

    salida = {
        "descripcion": "Reparto del centro histórico entre agentes. Coordenadas en metros del lienzo (X este, Y norte). "
        "Cada manzana tiene UN dueño: solo ese agente la modela. Fotos: el punto marca dónde está lo fotografiado.",
        "zona": {"xmin": xmin, "ymin": ymin, "xmax": xmax, "ymax": ymax},
        "frontera": {"calle": CALLE_FRONTERA, "punto": [round(mx, 1), round(my, 1)], "pendiente": round(pend, 4),
                      "regla": "centro de la manzana al norte de la recta -> claude; al sur -> codex"},
        "resumen": resumen,
        "manzanas": manzanas,
        "espacios": espacios,
        "fotos_espacio_publico": sin_edificio,
        "mobiliario": "Faroles, árboles y bancos de vereda: los modela el dueño de la manzana frente a la que están. "
                      "Los de la Plaza 25 de Mayo: dueño de P01.",
    }
    with open(os.path.join(SALIDA, "manzanas.json"), "w") as fh:
        json.dump(salida, fh, ensure_ascii=False, indent=1)

    dibujar(manzanas, calles, sin_edificio, fotos, (mx, my, pend))
    print(json.dumps(resumen, indent=1))


def dibujar(manzanas, calles, sin_edificio, fotos, frontera):
    xmin, ymin, xmax, ymax = ZONA
    m = 40
    esc = 3.0
    W, H = int((xmax - xmin) * esc) + 2 * m, int((ymax - ymin) * esc) + 2 * m
    img = Image.new("RGB", (W, H), "#f4f1ea")
    d = ImageDraw.Draw(img)

    def px(x, y):
        return (m + (x - xmin) * esc, m + (ymax - y) * esc)

    try:
        fuente = ImageFont.truetype("DejaVuSans.ttf", 13)
        chica = ImageFont.truetype("DejaVuSans.ttf", 10)
    except OSError:
        fuente = chica = ImageFont.load_default()
    for c in calles:
        d.line([px(*p) for p in c["pts"]], fill="#d8d0c0", width=int(6 * esc / 3))
    colores = {"claude": ("#f2b48a", "#b8541f"), "codex": ("#9cc3e6", "#2a5f94")}
    for mz in manzanas:
        relleno, borde = colores[mz["dueno"]]
        for e in mz["edificios"]:
            d.polygon([px(*p) for p in e["huella"]], fill=relleno, outline=borde)
    mx, my, pend = frontera
    d.line([px(xmin, my + pend * (xmin - mx)), px(xmax, my + pend * (xmax - mx))], fill="#c0392b", width=3)
    for u in fotos.values():
        x, y = px(u["x"], u["y"])
        d.ellipse([x - 2.5, y - 2.5, x + 2.5, y + 2.5], fill="#222")
    for mz in manzanas:
        if mz["area_m2"] > 150:
            x, y = px(*mz["centro"])
            d.text((x, y), mz["id"], fill="#111", font=chica, anchor="mm")
    nombres = set()
    for c in calles:
        if c["nombre"] and c["nombre"] not in nombres and c["tipo"] not in ("footway", "service"):
            pts = [p for p in c["pts"] if xmin <= p[0] <= xmax and ymin <= p[1] <= ymax]
            if len(pts) > 2:
                nombres.add(c["nombre"])
                x, y = px(*pts[len(pts) // 2])
                d.text((x, y), c["nombre"].replace("Calle ", ""), fill="#7a6f5c", font=chica, anchor="mm")
    d.rectangle([10, 10, 330, 78], fill="white", outline="#999")
    d.text((20, 16), "Naranja: Claude (norte)", fill=colores["claude"][1], font=fuente)
    d.text((20, 34), "Azul: Codex (sur)", fill=colores["codex"][1], font=fuente)
    d.text((20, 52), f"Rojo: frontera ({CALLE_FRONTERA.replace('Calle ', '')})", fill="#c0392b", font=chica)
    d.text((20, 64), "Puntos negros: fotos", fill="#222", font=chica)
    img.save(os.path.join(SALIDA, "reparto.png"))


main()
