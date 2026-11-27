"""AMP_N — ampliación norte: las esquinas al norte de la Av. Hernando Siles frente a la Calle Batalla de Junín
(correcciones R0060–R0062, 2026-11-13). Fuera de la zona original; reparto: espacio AMP_N, dueño claude.

Fotos: casonas coloniales blancas de 2 plantas con tejado de teja y alero, locales comerciales con toldos y letreros
en la planta baja, ventanas con reja y balcones de hierro arriba; detrás, un edificio de ladrillo visto de 3 plantas;
en la esquina NO, un árbol grande y un kiosco. La avenida es ancha (17 m).
Huellas: volúmenes del lienzo fuera de la zona (reparto → espacios → AMP_N → huellas_lienzo).
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit.datos import lados, recortar_a_calles  # noqa: E402
from mercado_claude import toldo  # noqa: E402
from piezas_claude import arbol, casa_sencilla, fachada, suelo_huella, techo_auto, tejado_dos_aguas  # noqa: E402

AGENTE, MID = "claude", "AMP_N"
m, col = iniciar(AGENTE, MID)
rnd = random.Random("amp-n")
LADRILLO = "#b0604a"
ESQUINA = (-112.0, 189.0)

for k, (poly, alto_l) in enumerate(zip(m["huellas_lienzo"], m["altos_lienzo"])):
    h = recortar_a_calles([tuple(p) for p in poly], area_min=12)
    if not h:
        continue
    zb, zr = suelo_huella(h)
    cx = sum(p[0] for p in h) / len(h)
    cy = sum(p[1] for p in h) / len(h)
    lejos = math.hypot(cx - ESQUINA[0], cy - ESQUINA[1])
    ladrillo = alto_l > 9 and 25 < lejos < 45 and k % 2 == 1          # el edificio de ladrillo de atrás (R0060)
    pisos = 3 if ladrillo else (2 if alto_l > 6 else 1)
    alto_piso = 3.6 if ladrillo else 4.2
    muro = LADRILLO if ladrillo else rnd.choice(["#f6f4ef", "#f4efe4", "#f6f4ef"])
    c = Constructor(f"AMP_N_{k}")
    c.huella = h
    c.prisma(h, zb - 0.6, zr + pisos * alto_piso, "muro", muro, tapa=False)
    if ladrillo:
        techo_auto(c, h, zr + pisos * alto_piso - 0.02, zpatio=zb, muro=("muro", muro))
    else:
        techo_auto(c, h, zr + pisos * alto_piso, zpatio=zb, muro=("muro", muro))
    for l in lados(h):
        if not l["a_calle"] or l["largo"] < 4:
            continue
        f = fachada(c, l)
        off = zr - f.suelo
        n = max(1, round(l["largo"] / 3.8))
        v = [l["largo"] * (j + 0.5) / n for j in range(n)]
        casa_sencilla(f, 0.0, l["largo"], pisos, alto_piso, off, muro=("muro", muro), zocalo_alto=0.9,
                      zocalo_color="#b98e6e", vanos=v, balcones=[x for x in v if rnd.random() < 0.5], puertas=v[::2],
                      remate="cornisa" if ladrillo else "alero", desde=zb - 0.6 - f.suelo, comercio=True)
        # locales con toldo en la planta baja de las casonas sobre la avenida y sobre Junín
        if not ladrillo and lejos < 40:
            for j in range(0, n, 2):
                toldo(f, v[j] - 1.6, v[j] + 1.6, off, rnd, vuelo=1.1)   # vereda de 2,6 m: toldo corto
    c.objeto(col)

# árbol grande y kiosco en la esquina NO de la avenida (R0062)
v = Constructor("AMP_N_esquina")
from kit.datos import calles_reales  # noqa: E402
# vereda norte de Hernando Siles, ~12 m al oeste del cruce con Junín (R0062): se toma el tramo del eje más cercano
_hs = [cc for cc in calles_reales() if cc["nombre"] == "Avenida Hernando Siles Zuaso"]
_mejor = None
for cc in _hs:
    for a_, b_ in zip(cc["eje"], cc["eje"][1:]):
        mx_, my_ = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
        dd = math.hypot(mx_ - ESQUINA[0], my_ - ESQUINA[1])
        if _mejor is None or dd < _mejor[0]:
            _mejor = (dd, a_, b_, cc)
_, a_, b_, cc = _mejor
L_ = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
u_ = ((b_[0] - a_[0]) / L_, (b_[1] - a_[1]) / L_)
n_ = (-u_[1], u_[0])
if n_[1] < 0:
    n_ = (-n_[0], -n_[1])                          # hacia el norte de la avenida
if u_[0] > 0:
    u_ = (-u_[0], -u_[1])                          # hacia el oeste
def _en_calzada(px, py, margen=0.0):
    for c2 in calles_reales():
        cz = c2["ancho"] / 2 - c2["vereda"] + margen
        for p_, q_ in zip(c2["eje"], c2["eje"][1:]):
            dx, dy = q_[0] - p_[0], q_[1] - p_[1]
            L2 = dx * dx + dy * dy or 1
            t = ((px - p_[0]) * dx + (py - p_[1]) * dy) / L2
            if 0 <= t <= 1 and math.hypot(px - p_[0] - t * dx, py - p_[1] - t * dy) < cz:
                return True
    return False


# se avanza desde el cruce hacia el norte de la avenida hasta salir de toda calzada (con 0,8 m de margen)
x = y = None
for k in range(0, 60):
    bx = ESQUINA[0] + u_[0] * 14.0 + n_[0] * (4.0 + k * 0.5)
    by = ESQUINA[1] + u_[1] * 14.0 + n_[1] * (4.0 + k * 0.5)
    if not _en_calzada(bx, by, 0.8) and not _en_calzada(bx + u_[0] * 2.4, by + u_[1] * 2.4, 0.8):
        x, y = bx, by
        break
if x is None:
    x, y = ESQUINA[0] + u_[0] * 14.0 + n_[0] * 12.0, ESQUINA[1] + u_[1] * 14.0 + n_[1] * 12.0
arbol(v, x, y, altura_suelo(x, y) + 0.18, alto=14.0, copa=8.0, semilla=62)
z = altura_suelo(x + u_[0] * 2.4, y + u_[1] * 2.4) + 0.18
kx, ky = x + u_[0] * 2.4, y + u_[1] * 2.4
v.caja(kx - 0.6, ky - 0.5, z, kx + 0.6, ky + 0.5, z + 2.3, "letrero", "#e9e5dc")              # kiosco junto al árbol
v.caja(kx - 0.7, ky - 0.6, z + 2.3, kx + 0.7, ky + 0.6, z + 2.45, "letrero", "#d9573a")
v.objeto(col)

from vecinos_claude import preparar  # noqa: E402
preparar(None, MID)   # recorte contra el muro del vecino (SIAMESES)
exportar(AGENTE, MID)
import json  # noqa: E402
CAMS = []
for rid in ("R0060", "R0061", "R0062"):
    e = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "coordinacion",
                                    "revisiones", rid, "revision.json")))["escena"]
    o = e["camara"]["lienzo"]
    rb = math.radians(e["camara"]["rumbo_grados"])
    CAMS.append((rid, (o["x"], o["y"], o["z"]), (o["x"] + math.sin(rb) * 15, o["y"] + math.cos(rb) * 15, o["z"] + 3)))
revisar(AGENTE, MID, fotos=[], camaras_extra=CAMS)
