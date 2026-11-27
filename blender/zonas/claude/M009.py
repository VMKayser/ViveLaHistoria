"""M009 — manzana NO de la esquina Ravelo × Batalla de Junín (frente a M020).

Fotos: 130237…130335 recorren la Calle Batalla de Junín desde la esquina con Ravelo hacia el SO.
Eje S sobre Junín: S = 0 en la esquina con Ravelo, creciendo hacia el SO (normal hacia la calle = SE).

S 0–10    TABOADA (esquina, obj E4d2575): 3 plantas, blanco, zócalo de piedra bajo, ventanas con balconcitos de
          hierro en 1.º y 2.º piso, cornisa (#1 #2; desde M020: 130234). Vuelta a Ravelo igual (sin foto directa).
S 10–18.4 DIVINA MODA (parte de E4d2575): 3 plantas; planta baja de sillería con dos portones; 1.º piso con
          banda de ladrillo, balcón de hierro y mirador de madera con antepecho de rombos; 2.º piso balcón; alero.
S 18.4–26 casas blancas de 2 plantas con mirador blanco (#3 #5 #6, «Foto Premier»), zócalo bajo rojizo.
S 26–37   casa blanca (parte NE de E8337fd, #9 #10): mirador de madera, pilastras, balcón de hierro, portones.
S 37–52.7 casona larga (parte SO de E8337fd, #11–#13): blanca con remates y claves rojos, balcones de hierro,
          pretil con pináculos rojos.
Frente a Ravelo (E647e35, E919282, E1ca428, E70f3f1, Eb7fc84): sin foto → casas coloniales sencillas.
Interiores: sin foto → volúmenes con tejado a dos aguas.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from piezas_claude import (techo_auto, lado_lienzo, adelantada, casa_sencilla, fachada, lado_virtual, mirador, partir_huella,  # noqa: E402
                           suelo_huella, tejado_dos_aguas)

AGENTE = "claude"
MANZANA = "M009"
m, col = iniciar(AGENTE, MANZANA)
E = {e["id"]: e for e in m["edificios"]}

# --- eje de Junín
l5 = lado_lienzo(E["E4d2575"], 5)
ESQ = l5["b"]
U = ((l5["a"][0] - l5["b"][0]) / l5["largo"], (l5["a"][1] - l5["b"][1]) / l5["largo"])  # hacia el SO
N = l5["normal"]


def P(S):
    return (ESQ[0] + U[0] * S, ESQ[1] + U[1] * S)


def frente(S0, S1):
    """Lado virtual sobre Junín entre S0 < S1 (a = S1 al SO, b = S0 al NE: misma orientación que las huellas)."""
    return lado_virtual(P(S1), P(S0), N)


def cortar(huella, S):
    """(parte NE con S < corte, parte SO)."""
    sw, ne = partir_huella(huella, ESQ, (-U[0], -U[1]), -S)
    return ne, sw


BLANCO = "#f6f4ef"
ZOC = "#b98e6e"
ROJO = "#c0533a"

# =========================================================================== E4d2575: Taboada + Divina Moda
taboada, divina = cortar(E["E4d2575"]["huella"], 10.0)

c = Constructor("E4d2575")
zb, zr = suelo_huella(taboada)
c.prisma(taboada, zb - 0.6, zr + 11.4, "muro", BLANCO, tapa=False)
techo_auto(c, taboada, zr + 11.38)
# fachada a Junín sobre el lado REAL de la casa esquina (auditoría: la esquina del lienzo cae en el corredor de
# Ravelo y la fachada recta invadía la calzada hasta 3 m)
_lj = [x for x in lados(taboada) if x["a_calle"] and x["calle"] == "Calle Batalla de Junín" and x["largo"] > 3]
f = fachada(c, max(_lj, key=lambda x: x["largo"]) if _lj else frente(0.0, 10.0))
_v = [f.largo * (k + 0.5) / 3 for k in range(3)]
casa_sencilla(f, 0.0, f.largo, 3, 3.6, zr - f.suelo, muro=("muro", BLANCO), zocalo_alto=1.1, zocalo_color=ZOC,
              vanos=_v, balcones=_v[1:], puertas=[_v[1]], desde=zb - 0.6 - f.suelo)
# R0079: miradores vidriados de marco blanco en los pisos altos de la esquina y letrero oscuro de la chocolatería
from piezas_claude import mirador as _mir  # noqa: E402
_off = zr - f.suelo
for _h in (3.6 + 0.4, 7.2 + 0.4):
    _mir(f, _v[0], _h + _off, ancho=2.6, alto=2.4, vuelo=0.85, base=("muro", BLANCO), madera=("marco_ventana", "#f2f2ee"),
         antepecho=("muro", BLANCO))
f.caja(0.2, f.largo - 0.2, 2.9 + _off, 3.5 + _off, 0.0, 0.22, "letrero", "#2a2320")
for _k in range(8):
    f.caja(0.8 + _k * 0.6, 1.1 + _k * 0.6, 3.05 + _off, 3.35 + _off, 0.22, 0.24, "letrero", "#c9a24a")
# vuelta a Ravelo (lado 0 de la huella original; solo el tramo de la casa esquina)
# sobre el lado REAL de la casa esquina que da a Ravelo (auditoría: con el lado del lienzo invadía Ravelo 2–3 m)
_lr = [x for x in lados(taboada) if x["a_calle"] and x["calle"] == "Calle Capitán Agustín Ravelo" and x["largo"] > 3]
l0 = max(_lr, key=lambda x: x["largo"]) if _lr else lado_lienzo(E["E4d2575"], 0, real=True)
fr = fachada(c, l0)
casa_sencilla(fr, 0.0, l0["largo"], 3, 3.6, zr - fr.suelo, muro=("muro", BLANCO), zocalo_alto=1.1, zocalo_color=ZOC,
              balcones=[l0["largo"] * k / 6 for k in range(1, 6, 2)], desde=zb - 0.6 - fr.suelo)

# Divina Moda
zb2, zr2 = suelo_huella(divina)
c.prisma(divina, zb2 - 0.6, zr2 + 10.2, "muro", BLANCO, tapa=False)
techo_auto(c, divina, zr2 + 10.18)
f = fachada(c, frente(10.0, 18.37))
off = zr2 - f.suelo
L = f.largo
zocalo(f, 3.4 + off, color="#c6a283", desde=zb2 - 0.6 - f.suelo)
fa = adelantada(f)
puerta(fa, 2.0, ancho=1.7, alto=2.9 + off, color="#5a2e1e", moldura="piedra", color_moldura="#c6a283")
puerta(fa, 6.6, ancho=1.3, alto=2.9 + off, color="#5a2e1e", moldura="piedra", color_moldura="#c6a283")
for h in (3.4, 6.6):  # bandas de ladrillo bajo cada balcón
    f.caja(0.0, L * 0.55, h + off, h + 0.5 + off, 0.0, 0.55, "piedra", "#b0583a")
    balcon_hierro(f, 0.1, L * 0.55 - 0.1, h + 0.5 + off, vuelo=0.55, losa="piedra", color_losa="#b0583a")
    ventana(f, L * 0.28, h + 0.5 + off, ancho=1.4, alto=2.1, moldura="moldura", color_moldura=BLANCO,
            carpinteria="marco_ventana", color_carpinteria="#5a2e1e")
mirador(f, L * 0.78, 3.9 + off, ancho=2.8, alto=2.2, vuelo=0.8, base=("muro", BLANCO),
        madera=("marco_ventana", "#6b3a26"), antepecho=("madera", "#8a4a2e"))
alero_tejas(f, 10.0 + off, vuelo=0.7, fondo=2.0)
c.objeto(col)

# =========================================================================== casas blancas S 18.4–26
for eid in ("E426fea", "Ebd9944", "E03497e"):
    c = Constructor(eid)
    h = E[eid]["huella"]
    zb, zr = suelo_huella(h)
    c.prisma(h, zb - 0.6, zr + 8.2, "muro", BLANCO, tapa=False)
    techo_auto(c, h, zr + 8.18)
    if eid == "E426fea":
        f = fachada(c, frente(18.4, 26.0))
        casa_sencilla(f, 0.0, f.largo, 2, 4.0, zr - f.suelo, muro=("muro", BLANCO), zocalo_color=ZOC,
                      vanos=[1.6, 4.2, 6.3], miradores=[4.2], puertas=[1.6], desde=zb - 0.6 - f.suelo)
    c.objeto(col)

# =========================================================================== E8337fd: casa con mirador + casona roja
ne, so = cortar(E["E8337fd"]["huella"], 37.0)
c = Constructor("E8337fd")
zb, zr = suelo_huella(E["E8337fd"]["huella"])
for h, alto in ((ne, 8.6), (so, 9.2)):
    c.prisma(h, zb - 0.6, zr + alto, "muro", BLANCO, tapa=False)
    techo_auto(c, h, zr + alto - 0.02)
f = fachada(c, frente(26.0, 37.0))
off = zr - f.suelo
casa_sencilla(f, 0.0, f.largo, 2, 4.3, off, muro=("muro", BLANCO), zocalo_color=ZOC, vanos=[1.5, 4.3, 7.4, 9.8],
              miradores=[4.3], balcones=[7.4], puertas=[1.5, 7.4], desde=zb - 0.6 - f.suelo)
for s in (0.2, 2.9, 5.8, 10.8):
    pilastra(f, s, 4.3 + off, 8.2 + off, ancho=0.4, vuelo=0.08, rol="moldura", color=BLANCO)
f = fachada(c, frente(37.0, 52.74))
off = zr - f.suelo
vanos = [1.2 + 2.25 * k for k in range(7)]
casa_sencilla(f, 0.0, f.largo, 2, 4.5, off, muro=("muro", BLANCO), zocalo_color=ZOC, vanos=vanos, balcones=vanos,
              puertas=[vanos[2], vanos[5]], remate="pinaculos", acento=ROJO, desde=zb - 0.6 - f.suelo)
for s in vanos:  # claves y ménsulas rojas sobre los vanos
    f.caja(s - 0.15, s + 0.15, 3.15 + off, 3.5 + off, 0.0, 0.1, "pintura_acento", ROJO)
    f.caja(s - 0.2, s + 0.2, 7.2 + off, 7.55 + off, 0.0, 0.12, "pintura_acento", ROJO)
c.objeto(col)

# =========================================================================== frente a Ravelo (sin foto)
for eid in ("E647e35", "E919282", "E1ca428", "E70f3f1", "Eb7fc84"):
    lc = [l["i"] for l in lados(E[eid]["huella"]) if l["a_calle"] and l["calle"] == "Calle Capitán Agustín Ravelo"]
    edificio_colonial(eid, E[eid]["huella"], pisos=2, alto_piso=4.2, color_muro="#f5f1e8", zocalo_alto=1.0,
                      remate="cornisa", lados_calle=lc, coleccion=col)

# =========================================================================== interiores (sin foto)
hechos = {"E4d2575", "E426fea", "Ebd9944", "E03497e", "E8337fd", "E647e35", "E919282", "E1ca428", "E70f3f1", "Eb7fc84"}
for eid, e in E.items():
    if eid in hechos:
        continue
    c = Constructor(eid)
    zb, zt = suelo_huella(e["huella"])
    alto = 6.5 if e["area_m2"] > 40 else 4.5
    c.prisma(e["huella"], zb - 0.6, zt + alto, "muro", "#efe8dc")
    tejado_dos_aguas(c, e["huella"], zt + alto, pendiente=24)
    c.objeto(col)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=())
detallar(col, m)
from vecinos_claude import preparar  # noqa: E402
preparar(None, MANZANA)   # recorte contra el muro del vecino (SIAMESES)
exportar(AGENTE, MANZANA)


def frontal(nombre, S, dist=9.0, alto_mira=5.0):
    p = P(S)
    z = altura_suelo(*p)
    return (nombre, (p[0] + N[0] * dist, p[1] + N[1] * dist, z + 1.7), (p[0], p[1], z + alto_mira))


cx, cy = m["centro"]
cz = altura_suelo(cx, cy)
revisar(AGENTE, MANZANA, fotos=["IMG_20261105_130250.jpg", "IMG_20261105_130325.jpg"] if "--todas" not in sys.argv else None,
        camaras_extra=[frontal("junin_esquina", 7.0, 7.5), frontal("junin_divina", 15.0),
                       frontal("junin_mirador", 30.0), frontal("junin_casona", 45.0, 11),
                       ("aerea", (cx + 50, cy - 50, cz + 55), (cx, cy, cz))])
