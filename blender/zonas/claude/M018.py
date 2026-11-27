"""M018 — Calle Batalla de Junín entre M009 y la Calle José Álvarez de Arenales (frontera con codex).

Fotos 130337…130344 (Ea7faac, Junín) y 130353…130359 (E1146d7, esquina Junín × Arenales):
continúa la casona blanca neoclásica de M009: 2 plantas, zócalo de sillería ~1.5 m, ventanas balconeras con
balcón de hierro y carpintería rojiza, claves y ménsulas rojas, medallones (óculos) rojos en la planta baja,
cortinas metálicas grises en los portones de tienda, pretil con pináculos rojos.
Esquina Junín × Arenales: mirador de madera rojiza en el 1.er piso, sobre la esquina.
Frente a Arenales (E1146d7 lado 5): sin foto de frente; en #7 se ve muro blanco con alero de tejas → casa sencilla.
El templo de San Miguel que aparece al fondo (#4–#7) está al otro lado de Arenales: no es de esta manzana.
Interiores: sin foto.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from piezas_claude import lado_lienzo, techo_auto, casa_sencilla, fachada, mirador, suelo_huella, tejado_dos_aguas  # noqa: E402

AGENTE = "claude"
MANZANA = "M018"
m, col = iniciar(AGENTE, MANZANA)
E = {e["id"]: e for e in m["edificios"]}
BLANCO = "#f6f4ef"
ROJO = "#c0533a"
ZOC = "#b98e6e"
MADERA_ROJA = "#7a3a2a"


def casona_roja(f, off, desde, n=None, cortinas=()):
    L = f.largo
    n = n or max(2, round(L / 4.4))
    vanos = [L * (k + 0.5) / n for k in range(n)]
    casa_sencilla(f, 0.0, L, 2, 4.5, off, muro=("muro", BLANCO), zocalo_alto=1.5, zocalo_color=ZOC, vanos=vanos,
                  balcones=vanos, puertas=[vanos[k] for k in cortinas], remate="pinaculos", acento=ROJO,
                  carpinteria=("marco_ventana", MADERA_ROJA), desde=desde)
    for k, s in enumerate(vanos):
        f.caja(s - 0.15, s + 0.15, 3.15 + off, 3.5 + off, 0.0, 0.1, "pintura_acento", ROJO)    # clave
        f.caja(s - 0.25, s + 0.25, 7.3 + off, 7.65 + off, 0.0, 0.12, "pintura_acento", ROJO)   # ménsula alta
        if k < n - 1:                                                                          # medallón rojo
            sm = (s + vanos[k + 1]) / 2
            f.arco(sm, 0.22, 0.09, 2.6 + off, 0.0, 0.06, "pintura_acento", ROJO, segmentos=8, medio=False)
    for k in cortinas:  # cortina metálica gris dentro del portón
        f.caja(vanos[k] - 0.7, vanos[k] + 0.7, 0.0, 2.9 + off, 0.07, 0.11, "metal", "#9a9c9c")
    return vanos


# =========================================================================== Ea7faac (Junín, fotos #1–#3)
e = E["Ea7faac"]
c = Constructor("Ea7faac")
zb, zr = suelo_huella(e["huella"])
c.prisma(e["huella"], zb - 0.6, zr + 9.0, "muro", BLANCO, tapa=False)
techo_auto(c, e["huella"], zr + 8.98)
l = lado_lienzo(e, 3)
f = fachada(c, l)
casona_roja(f, zr - f.suelo, zb - 0.6 - f.suelo, n=6, cortinas=(1, 4))
c.objeto(col)

# =========================================================================== E1146d7 (esquina Junín × Arenales)
e = E["E1146d7"]
c = Constructor("E1146d7")
zb, zr = suelo_huella(e["huella"])
c.prisma(e["huella"], zb - 0.6, zr + 9.0, "muro", BLANCO, tapa=False)
techo_auto(c, e["huella"], zr + 8.98)
# Corrección R0038 ("glitches en esta esquina"): las fachadas iban sobre los lados del lienzo corridos en recto y en
# la esquina quedaban pretiles y pináculos flotando fuera del volumen. Ahora van sobre los lados REALES de la huella
# recortada, y Arenales lleva el mismo tratamiento de casona (pináculos y claves rojos) que se ve en la foto.
def lado_real(h, calle):
    cand = [x for x in lados(h) if x["a_calle"] and x["calle"] == calle and x["largo"] >= 3.0]
    return max(cand, key=lambda x: x["largo"]) if cand else None


lj = lado_real(e["huella"], "Calle Batalla de Junín")
la = lado_real(e["huella"], "Calle José Álvarez de Arenales")
ls = {6: lj or lado_lienzo(e, 6), 5: la or lado_lienzo(e, 5)}
f = fachada(c, ls[6])                       # Junín
off = zr - f.suelo
vanos = casona_roja(f, off, zb - 0.6 - f.suelo, n=7, cortinas=(2, 5))
# la esquina con Arenales: el extremo del lado de Junín más cercano al lado de Arenales
ma = ((ls[5]["a"][0] + ls[5]["b"][0]) / 2, (ls[5]["a"][1] + ls[5]["b"][1]) / 2)
db = math.hypot(ls[6]["b"][0] - ma[0], ls[6]["b"][1] - ma[1])
da = math.hypot(ls[6]["a"][0] - ma[0], ls[6]["a"][1] - ma[1])
esquina_s = f.largo if db < da else 0.0
mirador(f, esquina_s - 1.6 if esquina_s else 1.6, 4.9 + off, ancho=2.6, alto=2.4, vuelo=0.9, base=("muro", BLANCO),
        madera=("marco_ventana", MADERA_ROJA), antepecho=("madera", MADERA_ROJA))
f = fachada(c, ls[5])                       # Arenales
casona_roja(f, zr - f.suelo, zb - 0.6 - f.suelo, cortinas=(1,))
c.objeto(col)

# =========================================================================== frente a Ravelo (Eafb768, sin foto) e interiores
edificio_colonial("Eafb768", E["Eafb768"]["huella"], pisos=2, alto_piso=4.2, color_muro="#f5f1e8",
                  coleccion=col)
for eid, e in E.items():
    if eid in ("Ea7faac", "E1146d7", "Eafb768"):
        continue
    c = Constructor(eid)
    zb, zt = suelo_huella(e["huella"])
    alto = 7.0 if e["area_m2"] > 150 else (6.0 if e["area_m2"] > 40 else 4.5)
    c.prisma(e["huella"], zb - 0.6, zt + alto, "muro", "#efe8dc")
    if e["area_m2"] > 600:
        techo_auto(c, e["huella"], zt + alto + 0.01)
    else:
        tejado_dos_aguas(c, e["huella"], zt + alto, pendiente=24)
    c.objeto(col)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=())
detallar(col, m)
from vecinos_claude import preparar  # noqa: E402
preparar(None, MANZANA)   # recorte contra el muro del vecino (SIAMESES)
exportar(AGENTE, MANZANA)
l6 = ls[6]
p = (l6["b"][0], l6["b"][1])
z = altura_suelo(*p)
n6 = l6["normal"]
pm = ((l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2)
revisar(AGENTE, MANZANA, fotos=["IMG_20261105_130341.jpg", "IMG_20261105_130354.jpg"] if "--todas" not in sys.argv else None,
        camaras_extra=[("esquina", (p[0] + n6[0] * 9 - 6 * (l6["a"][0] - p[0]) / l6["largo"],
                                    p[1] + n6[1] * 9 - 6 * (l6["a"][1] - p[1]) / l6["largo"], z + 1.7), (p[0], p[1], z + 5)),
                       ("junin", (pm[0] + l["normal"][0] * 8, pm[1] + l["normal"][1] * 8, altura_suelo(*pm) + 1.7),
                        (pm[0], pm[1], altura_suelo(*pm) + 5)),
                       ("R0038", (-291.38, -37.31, 57.14), (-302.6, -9.82, 58.15)),
                       ("aerea", (m["centro"][0] + 50, m["centro"][1] - 45, z + 55), (*m["centro"], z))])
