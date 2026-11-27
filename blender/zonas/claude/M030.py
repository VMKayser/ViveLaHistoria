"""M030 — lado SO de Ravelo entre M020 y la Calle Aniceto Arce, y frente a Arce.

Incluye el HUECO del lienzo sobre Ravelo (entre la punta SE de M020 y la huella E530f95), que en la realidad
está construido. Eje S a lo largo de Ravelo: S = 0 en la punta SE de M020 (Ef32a68), negativo hacia el SE.

Fotos: 125849/125853 (fin de la casa blanca de M020 y Farmacia La Plata), 125900, 125904, 125909 (CNS),
125918/125924/125929 (CNS de frente), 125934…125945 (Central Mall y esquina), 125950 (esquina con Arce).

FARMACIA LA PLATA (S 0 → −13, huella propia en el hueco): neoclásica, 3 vanos, sillería en planta baja,
  ventanas balconeras con frontón, muro blanco, molduras gris azulado.
CNS — Policlínico 25 de Mayo (S −13 → −55: hueco + parte NO de E530f95): igual lenguaje, 9 vanos, portal central
  con medallón «CNS», planta baja toda de sillería con ventanas enrejadas, pretil con tableros. ~10.4 m.
CENTRAL MALL (S −55 → −68.6, parte SE de E530f95): moderno, 2 plantas (~8.5 m), escaparates, franja vertical
  marrón en la entrada, banda de vidrio arriba.
ESQUINA ARCE (S −68.6 → −86, huella propia): 3 plantas modernas acristaladas (Juguetería / Prendamás).
  El toldo amarillo de la terraza se omite (regla de estilo).
Lado Arce (Ee1612b, Eb4d256 Casa de la Cultura): sin foto → versiones coloniales sencillas.
Interiores E9f7279, E5b5520: sin foto.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from piezas_claude import (techo_auto, lado_lienzo, fachada, fachada_moderna, fachada_neoclasica, lado_virtual, partir_huella,  # noqa: E402
                           suelo_huella, tejado_dos_aguas)

AGENTE = "claude"
MANZANA = "M030"
m, col = iniciar(AGENTE, MANZANA)
E = {e["id"]: e for e in m["edificios"]}

# --- eje de Ravelo
PUNTA = (-187.47, 34.8)                      # punta SE de M020 (Ef32a68, lado 5, a)
l0 = lado_lienzo(E["E530f95"], 0)  # a = SE (S −68.6), b = NO (S −27.1)
U = ((l0["b"][0] - l0["a"][0]) / l0["largo"], (l0["b"][1] - l0["a"][1]) / l0["largo"])  # hacia el NO
N = l0["normal"]                              # hacia la calle


def P(S, prof=0.0):
    """Punto sobre la línea de fachada de Ravelo a la distancia S (y 'prof' metros hacia adentro)."""
    # la línea pasa por la punta de M020 y por E530f95.a; se interpola el pequeño desvío lateral
    a_s = (l0["a"][0] - PUNTA[0]) * U[0] + (l0["a"][1] - PUNTA[1]) * U[1]
    a_p = (l0["a"][0] - PUNTA[0]) * N[0] + (l0["a"][1] - PUNTA[1]) * N[1]
    lat = a_p * (S / a_s)
    return (PUNTA[0] + U[0] * S + N[0] * (lat - prof), PUNTA[1] + U[1] * S + N[1] * (lat - prof))


# La línea del lienzo queda ~1 m dentro del corredor real de Ravelo (auditoría 2026-11-12: el zócalo invadía la
# vereda y la dejaba en 0,9 m). Se corre toda la línea hacia adentro lo que haga falta para que nada la cruce.
def _penetracion(x, y):
    from kit.datos import calles_reales as _cr
    pen = 0.0
    for cc in _cr():
        if cc["nombre"] != "Calle Capitán Agustín Ravelo":
            continue
        w = cc["ancho"] / 2
        for a_, b_ in zip(cc["eje"], cc["eje"][1:]):
            dx, dy = b_[0] - a_[0], b_[1] - a_[1]
            L2 = dx * dx + dy * dy or 1
            t = ((x - a_[0]) * dx + (y - a_[1]) * dy) / L2
            if 0 <= t <= 1:
                pen = max(pen, w - math.hypot(x - a_[0] - t * dx, y - a_[1] - t * dy))
    return pen


_P0 = P
RETRO = max(_penetracion(*_P0(S_)) for S_ in [-86.0 + k * 0.5 for k in range(173)]) + 0.05
print("[M030] la línea de fachada se corre", round(RETRO, 2), "m hacia adentro")


def P(S, prof=0.0):  # noqa: F811
    return _P0(S, prof + RETRO)


def huella_frente(S_no, S_se, prof):
    return [P(S_se), P(S_no), P(S_no, prof), P(S_se, prof)]


def frente(S_no, S_se):
    return lado_virtual(P(S_se), P(S_no), N)


BLANCO = "#f4f3ef"
GRIS = "#c3ccd6"
SILLAR = "#c4a181"

# =========================================================================== FARMACIA LA PLATA (hueco)
h_far = huella_frente(-0.7, -13.0, 12.8)  # (0, 14) hasta el ensanche de Ravelo: la línea se corrió 0,5 m y el alero de M020 entraba
c = Constructor("M030_farmacia_la_plata")
zb, zr = suelo_huella(h_far)
c.prisma(h_far, zb - 0.6, zr + 10.2, "muro", BLANCO, tapa=False)
techo_auto(c, h_far, zr + 10.18)
f = fachada(c, frente(-0.7, -13.0))
fachada_neoclasica(f, 0.0, f.largo, 3, zr - f.suelo, alto_total=10.2, muro=("muro", BLANCO), moldura=("moldura", GRIS),
                   sillar=SILLAR, desde=zb - 0.6 - f.suelo)
c.objeto(col)

# =========================================================================== CNS (hueco + parte NO de E530f95)
S_MALL = -55.0
s_corte = (P(S_MALL)[0] - l0["a"][0]) * U[0] + (P(S_MALL)[1] - l0["a"][1]) * U[1]
parte_mall, parte_cns = partir_huella(E["E530f95"]["huella"], l0["a"], U, s_corte)
# las partes del lienzo se recortan a la línea de fachada corrida (si no, su cara tapa las fachadas)
from kit.datos import _cortar_semiplano  # noqa: E402


def _detras(h, S0, S1):
    """Deja la parte de h detrás de la línea de fachada entre P(S0) y P(S1) (la línea gira un poco: se usa la recta
    exacta del tramo, con un margen de 2 cm)."""
    q0, q1 = P(S0), P(S1)
    L_ = math.hypot(q1[0] - q0[0], q1[1] - q0[1])
    nx_, ny_ = -(q1[1] - q0[1]) / L_, (q1[0] - q0[0]) / L_
    if nx_ * N[0] + ny_ * N[1] > 0:
        nx_, ny_ = -nx_, -ny_                 # hacia adentro
    r = _cortar_semiplano(h, q0[0], q0[1], nx_, ny_, 0.02)
    return r if len(r) >= 3 else h


parte_cns = _detras(parte_cns, -13.0, S_MALL)
parte_mall = _detras(parte_mall, S_MALL, -68.6)
h_cns_hueco = huella_frente(-13.0, -27.1, 15.2)   # 16 m hasta el ensanche de Ravelo (la fachada se corrió hacia M020)
c = Constructor("E530f95")
zb = min(suelo_huella(parte_cns)[0], suelo_huella(h_cns_hueco)[0])
zr = max(suelo_huella(parte_cns)[1], suelo_huella(h_cns_hueco)[1])
for h in (h_cns_hueco, parte_cns):
    c.prisma(h, zb - 0.6, zr + 10.4, "muro", BLANCO, tapa=False)
    techo_auto(c, h, zr + 10.38)
f = fachada(c, frente(-13.0, S_MALL))
fachada_neoclasica(f, 0.0, f.largo, 9, zr - f.suelo, alto_total=10.4, portal=4, medallon=True, muro=("muro", BLANCO),
                   moldura=("moldura", GRIS), sillar=SILLAR, desde=zb - 0.6 - f.suelo)
c.objeto(col)

# =========================================================================== CENTRAL MALL (parte SE de E530f95)
c = Constructor("E530f95_central_mall")
zb, zr = suelo_huella(parte_mall)
c.prisma(parte_mall, zb - 0.6, zr + 8.5, "muro", "#f2f2ef", tapa=False)
techo_plano(c, parte_mall, zr + 8.48)
f = fachada(c, frente(S_MALL, -68.6))
off = zr - f.suelo
fachada_moderna(f, 0.0, f.largo, 2, 4.0, off)
# franja vertical marrón (revestimiento tipo madera) en la entrada, con panel claro
s_m = f.largo * 0.35
f.caja(s_m - 2.0, s_m + 2.0, 0.0, 8.6 + off, 0.0, 0.35, "madera", "#8b4a2b")
f.caja(s_m - 1.3, s_m + 1.3, 4.2 + off, 6.9 + off, 0.35, 0.4, "letrero")
f.caja(s_m - 1.3, s_m + 1.3, 0.0, 3.2 + off, 0.3, 0.37, "vidrio")
c.objeto(col)

# =========================================================================== ESQUINA ARCE (huella propia)
h_esq = huella_frente(-68.6, -86.0, 10.0)
c = Constructor("M030_esquina_arce")
zb, zr = suelo_huella(h_esq)
c.prisma(h_esq, zb - 0.6, zr + 10.5, "muro", "#f3f3f0", tapa=False)
techo_plano(c, h_esq, zr + 10.48)
f = fachada(c, frente(-68.6, -86.0))
fachada_moderna(f, 0.0, f.largo, 3, 3.4, zr - f.suelo, vuelo_losas=0.8)
# esquina hacia Arce (lado corto del SE)
lado_arce = lado_virtual(P(-86.0), P(-86.0, 10.0), (-U[0], -U[1]))
fa = fachada(c, lado_arce)
fachada_moderna(fa, 0.0, fa.largo, 3, 3.4, zr - fa.suelo, vuelo_losas=0.8)
c.objeto(col)

# =========================================================================== lado Arce (sin foto)
edificio_colonial("Ee1612b", E["Ee1612b"]["huella"], pisos=2, alto_piso=4.3, color_muro="#f1ece2", zocalo_alto=1.3,
                  remate="cornisa", coleccion=col)
edificio_colonial("Eb4d256", E["Eb4d256"]["huella"], pisos=2, alto_piso=4.5, color_muro="#f3e6d3", zocalo_alto=1.5,
                  remate="alero", coleccion=col)
from shapely.geometry import Polygon  # noqa: E402
# la casa interior E5b5520 (sin foto) cae en parte bajo el CNS (su hueco de 16 m de fondo): se recorta contra él
_cns = (Polygon([tuple(p[:2]) for p in parte_cns]).union(Polygon([tuple(p[:2]) for p in h_cns_hueco]))
        .union(Polygon([tuple(p[:2]) for p in parte_mall])).buffer(0.05))         # volúmenes reales del CNS y el mall
for eid, alto in (("E9f7279", 5.5), ("E5b5520", 7.5)):
    c = Constructor(eid)
    h = E[eid]["huella"]
    if eid == "E5b5520":
        resto = Polygon([tuple(p[:2]) for p in h]).difference(_cns)
        resto = max(getattr(resto, "geoms", [resto]), key=lambda g: g.area)
        h = [list(p) for p in list(resto.exterior.coords)[:-1]]
        print("[M030] E5b5520 recortada contra el CNS:", round(Polygon([tuple(p[:2]) for p in E[eid]["huella"]]).area, 1), "→", round(resto.area, 1), "m²")
    zb, zt = suelo_huella(h)
    c.prisma(h, zb - 0.6, zt + alto, "muro", "#efe8dc")
    tejado_dos_aguas(c, h, zt + alto, pendiente=24)
    c.objeto(col)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=("E530f95_central_mall", "M030_esquina_arce"))
detallar(col, m)
from vecinos_claude import preparar  # noqa: E402
preparar(col, MANZANA)
# E5b5520 (anexo interior sin foto) queda en la muesca en U del CNS: tocan pared con pared, pero calidad.py la ve "encerrada"
# (sus rayos en las 4 direcciones chocan con el CNS) y la marca SIAMESES. Es parte del mismo conjunto: va en el mismo objeto.
import bpy  # noqa: E402
_cns_ob, _anexo = bpy.data.objects["E530f95"], bpy.data.objects["E5b5520"]
with bpy.context.temp_override(active_object=_cns_ob, selected_editable_objects=[_cns_ob, _anexo]):
    bpy.ops.object.join()
exportar(AGENTE, MANZANA)

FOTOS = ["IMG_20261105_125918.jpg"]
cam = P(-30.0)
cz = altura_suelo(*cam)
def frontal(nombre, S, dist=9.0, alto_mira=5.0):
    p = P(S)
    z = altura_suelo(*p)
    return (nombre, (p[0] + N[0] * dist, p[1] + N[1] * dist, z + 1.7), (p[0], p[1], z + alto_mira))


revisar(AGENTE, MANZANA, fotos=FOTOS if "--todas" not in sys.argv else None,
        camaras_extra=[frontal("frente_farmacia_cns", -12.0), frontal("frente_cns_portal", -34.0),
                       frontal("frente_mall_esquina", -70.0),
                       ("aerea", (cam[0] + N[0] * 60 + U[0] * 20, cam[1] + N[1] * 60 + U[1] * 20, cz + 60),
                        (cam[0], cam[1], cz))])
