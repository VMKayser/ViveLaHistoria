"""Trazado de una SECCIÓN (refactor 2026-11-14, pedido del usuario: "modelar zona por zona, guiándonos con
OpenStreetMap"). Geometría 2D limpia con shapely, sin parches:

  calzada  = unión de las franjas de calzada de cada calle (ejes de calles_reales = OSM corrido a las fachadas)
  plaza    = polígono del espacio (P01) — lo modela su dueño
  vereda   = TODO lo demás dentro de la sección (llega siempre hasta las fachadas: no puede quedar hueco)
  bordillo = borde común vereda/calzada, con esquinas redondeadas (radio R_ESQUINA)

Se usa desde Blender (shapely instalado en el Python de Blender) y desde python3 para planos de control.
"""

import json
import math
import os

from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.ops import unary_union

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
R_ESQUINA = 2.5          # radio del bordillo en las esquinas (m)
SUAVIZAR = 1.2           # quita mellas de los bordillos (ejes de OSM con quiebres de pocos grados)
VEREDA_PLAZA = 3.0       # vereda propia alrededor de la plaza (lado de la plaza de las calles que la rodean)
FONDO_VEREDA = 3.0       # la vereda sigue este tanto por detrás de la línea de fachada (queda bajo los edificios)
HASTA_FACHADA = 10.0     # además, el suelo libre hasta las fachadas reales, si las hay a menos de esto del corredor
PROLONGAR = 6.0          # cada eje se prolonga en sus extremos para que el cruce quede cubierto


def _json(rel):
    with open(os.path.join(RAIZ, rel)) as fh:
        return json.load(fh)


def cargar_seccion(nombre):
    return _json(f"secciones/{nombre}.json")


def _prolongado(eje, d):
    (x0, y0), (x1, y1) = eje[0], eje[1]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    a = (x0 - (x1 - x0) / L * d, y0 - (y1 - y0) / L * d)
    (x0, y0), (x1, y1) = eje[-2], eje[-1]
    L = math.hypot(x1 - x0, y1 - y0) or 1
    b = (x1 + (x1 - x0) / L * d, y1 + (y1 - y0) / L * d)
    return [a] + [tuple(p) for p in eje] + [b]


def _edificios_recortados():
    """Huellas recortadas del lienzo (kit/datos.py, cargado sin el resto del kit para servir también fuera de Blender)."""
    import importlib.util
    sp = importlib.util.spec_from_file_location("_datos_kit", os.path.join(RAIZ, "blender", "kit", "datos.py"))
    d = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(d)
    return d.edificios_recortados()


def trazar(sec):
    """Devuelve dict de geometrías shapely: limite, calzada, vereda, plaza, calles[(nombre, eje, medio_calzada)]."""
    limite = Polygon(sec["limite"])
    espacios = {e["id"]: e for e in _json("reparto/manzanas.json")["espacios"]}
    plaza = Polygon(espacios[sec["plaza"]]["poligono"]) if sec.get("plaza") else Polygon()
    calles = []
    franjas = []
    corredores = []
    hondos = []
    for c in _json("reparto/calles_reales.json")["calles"]:
        if c["nombre"] not in sec["calles"]:
            continue
        eje = LineString(c["eje"])
        if not eje.intersects(limite.buffer(20)):
            continue
        vi = c.get("vereda_izq", c["vereda"])
        vd = c.get("vereda_der", c["vereda"])
        medio = (c["ancho"] - vi - vd) / 2
        ancho_calzada = sec.get("calzadas", {}).get(c["nombre"], 2 * medio)
        e = LineString(_prolongado(c["eje"], PROLONGAR))
        franjas.append(e.buffer(ancho_calzada / 2, cap_style="flat", join_style="mitre", mitre_limit=3))
        corredores.append(e.buffer(c["ancho"] / 2 + FONDO_VEREDA, cap_style="flat", join_style="mitre", mitre_limit=3))
        hondos.append(e.buffer(c["ancho"] / 2 + HASTA_FACHADA, cap_style="flat", join_style="mitre", mitre_limit=3))
        calles.append((c["nombre"], c["eje"], ancho_calzada / 2))
    borde_plaza = plaza.buffer(VEREDA_PLAZA, join_style="mitre") if not plaza.is_empty else plaza
    # se suaviza con la calzada prolongada más allá del límite y se recorta después: si no, el corte contra el límite
    # quedaba redondeado y el bordillo se curvaba hacia la calzada donde empalma con la BASE (R0228)
    calzada = unary_union(franjas).difference(borde_plaza).intersection(limite.buffer(15, join_style="mitre"))
    # esquinas: cerrar la calzada redondea las esquinas de vereda (radio R_ESQUINA); abrirla un poco quita las
    # mellas. Las franjas finas de vereda (la de la plaza, 3 m) no se tocan.
    calzada = calzada.buffer(R_ESQUINA, join_style="round").buffer(-R_ESQUINA, join_style="round")
    calzada = calzada.buffer(-SUAVIZAR, join_style="round").buffer(SUAVIZAR, join_style="round")
    calzada = calzada.intersection(limite).difference(borde_plaza)
    # la vereda acompaña a las calles (hasta FONDO_VEREDA m detrás de la línea de fachada, para llegar a las fachadas
    # algo retiradas); los lotes del interior de la cuadra NO se pavimentan (se veían como plazas vacías)
    zona_vereda = unary_union(corredores + [borde_plaza]).intersection(limite)
    vereda = zona_vereda.difference(calzada).difference(plaza)
    # el recorte de las huellas (kit.datos.recortar_a_calles) corta por semiplanos y, en las esquinas en ángulo, retira
    # la fachada más allá del corredor: entre la vereda y el edificio quedaba un hueco sin suelo (revisión por MCP,
    # 2026-11-24, esquina Arenales × Arce). Se pavimenta el suelo libre que toca la vereda hasta las fachadas reales.
    edif = unary_union([Polygon(h).buffer(0) for h in _edificios_recortados()])
    libre = unary_union(hondos).intersection(limite).difference(edif).difference(calzada).difference(plaza)
    libre = libre.difference(vereda)
    pegados = [q for q in (libre.geoms if hasattr(libre, "geoms") else [libre])
               if not q.is_empty and q.area > 0.5 and q.distance(vereda) < 0.05]
    if pegados:
        vereda = unary_union([vereda] + pegados)
    return {"limite": limite, "plaza": plaza, "calzada": calzada, "vereda": vereda, "calles": calles}


def plano_png(nombre, ruta, extra=()):
    """Plano de control de la sección (python3 con Pillow)."""
    from PIL import Image, ImageDraw
    sec = cargar_seccion(nombre)
    g = trazar(sec)
    x0, y0, x1, y1 = g["limite"].bounds
    E = 4.0
    im = Image.new("RGB", (int((x1 - x0) * E) + 1, int((y1 - y0) * E) + 1), "white")
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((x - x0) * E, (y1 - y) * E)

    def pinta(geom, fill, outline=None):
        polys = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        for p in polys:
            if p.is_empty or p.geom_type != "Polygon":
                continue
            d.polygon([P(*q) for q in p.exterior.coords], fill=fill, outline=outline)
            for h in p.interiors:
                d.polygon([P(*q) for q in h.coords], fill="white")
    pinta(g["vereda"], (205, 200, 192), (120, 110, 100))
    pinta(g["calzada"], (110, 110, 115))
    pinta(g["plaza"], (150, 200, 140))
    for (x, y, txt) in extra:
        d.ellipse([P(x, y)[0] - 3, P(x, y)[1] - 3, P(x, y)[0] + 3, P(x, y)[1] + 3], fill="red")
        d.text(P(x, y), txt, fill="red")
    im.save(ruta)
