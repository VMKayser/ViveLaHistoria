"""M021 — frente del Mercado Central sobre Ravelo (lado NE), huella E78df12.

Fotos 130158…130224: edificio blanco de 2 plantas. Planta alta: fila de grandes ventanales de medio punto
vidriados con cuadrícula, sobre muro liso. Planta baja: arcada de tiendas (arcos de medio punto). Pretil liso con
faroles. Delante, en la vereda de Ravelo, una fila de árboles de copa redonda. Los extremos (lados 0 y 2) repiten
el orden. Se omiten letreros comerciales.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from piezas_claude import techo_auto, adelantada, arbol, arbol_paraguas, fachada, junto_al_bordillo, suelo_huella  # noqa: E402
from mercado_claude import luneto, tienda  # noqa: E402
import random  # noqa: E402
RND = random.Random("mercado-ravelo")

AGENTE = "claude"
MANZANA = "M021"
m, col = iniciar(AGENTE, MANZANA)
e = m["edificios"][0]
BLANCO = "#f5f4f0"
ALTO = 9.2

c = Constructor(e["id"])
zb, zr = suelo_huella(e["huella"])
c.prisma(e["huella"], zb - 0.6, zr + ALTO, "muro", BLANCO, tapa=False)
techo_auto(c, e["huella"], zr + ALTO - 0.02)


def fachada_mercado(f, n):
    off = zr - f.suelo
    paso = f.largo / n
    zocalo(f, 0.5 + off, color="#b3a493", sillares=False, desde=zb - 0.6 - f.suelo)
    # locales ABIERTOS con mercadería y toldo (corrección R0046: "no son de vidrio, son negocios") y lunetos arriba
    for k in range(n):
        s = paso * (k + 0.5)
        tienda(f, s - paso / 2, s + paso / 2, off, RND, vuelo=1.4)
        luneto(f, s, off, r=min(1.45, paso / 2 - 0.4))
        if k:
            f.caja(paso * k - 0.2, paso * k + 0.2, 0.0, ALTO - 0.6 + off, 0.0, 0.14, "moldura", BLANCO)
    imposta(f, 4.5 + off, alto=0.2, vuelo=0.1, color=BLANCO)
    cornisa(f, ALTO - 0.6 + off, vuelo=0.2, alto=0.3, color=BLANCO)
    parapeto(f, ALTO - 0.3 + off, alto=0.4, color=BLANCO)


# frente a Ravelo: con la calle ensanchada la huella recortada sigue el eje curvo en varios lados (R0129: con solo el
# "lado 1" del lienzo quedaba un muro ciego de 16 m); cada lado a Ravelo lleva sus locales, ~4 m por local
LADOS = lados(e["huella"])
RAVELO = [l for l in LADOS if "Ravelo" in l["calle"] and l["largo"] > 2.0]
for l_ in RAVELO:
    fachada_mercado(fachada(c, l_), max(1, round(l_["largo"] / 4.0)))
for l_ in LADOS:                                  # extremos (a las calles transversales)
    if l_["a_calle"] and "Ravelo" not in l_["calle"] and l_["largo"] < 12:
        fachada_mercado(fachada(c, l_), 2)
c.objeto(col)

# árboles de la vereda de Ravelo, junto al bordillo (uno cada ~6,5 m del frente)
ca = Constructor("M021_arboles")
k = 0
for l in RAVELO:
    ux, uy = (l["b"][0] - l["a"][0]) / l["largo"], (l["b"][1] - l["a"][1]) / l["largo"]
    n_ = max(1, round(l["largo"] / 6.5)) if l["largo"] > 5 else 0
    for j in range(n_):
        t = l["largo"] * (j + 0.5) / n_
        # junto al BORDILLO (usuario R0107/R0109/R0130: "árboles siempre cerca del borde de la acera"), con paso
        # libre hasta los puestos del mercado
        x, y = junto_al_bordillo(l["a"][0] + ux * t, l["a"][1] + uy * t, *l["normal"], retiro=0.55)
        zv = altura_suelo(x, y) + 0.25
        arbol_paraguas(ca, x, y, zv, alto=5.4, copa=4.4, semilla=k,
                       desplazar=(l["normal"][0] * 0.6, l["normal"][1] * 0.6))
        # banco de madera junto al árbol, en su misma línea
        if t + 2.4 < l["largo"]:
            bx, by = x + ux * 2.2, y + uy * 2.2
            zb_ = altura_suelo(bx, by) + 0.25
            nx, ny = l["normal"]
            ca.caja_ejes((bx, by, zb_ + 0.44), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 1.6, 0.42, 0.06, "madera", "#6e4a2e")
            ca.caja_ejes((bx + nx * 0.2, by + ny * 0.2, zb_ + 0.72), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 1.6, 0.05, 0.4, "madera", "#6e4a2e")
            for sgn in (-0.65, 0.65):
                ca.caja_ejes((bx + ux * sgn, by + uy * sgn, zb_ + 0.22), (ux, uy, 0), (nx, ny, 0), (0, 0, 1), 0.06, 0.42, 0.44, "hierro")
        k += 1
l = max(RAVELO, key=lambda x: x["largo"])
ux, uy = (l["b"][0] - l["a"][0]) / l["largo"], (l["b"][1] - l["a"][1]) / l["largo"]
# faroles coloniales de pared en las esquinas del frente (foto 130213)
for t in (0.6, l["largo"] - 0.6):
    x = l["a"][0] + ux * t
    y = l["a"][1] + uy * t
    nx, ny = l["normal"]
    zf = altura_suelo(x, y) + 7.6
    ca.caja_ejes((x + nx * 0.4, y + ny * 0.4, zf + 0.3), (nx, ny, 0), (ux, uy, 0), (0, 0, 1), 0.8, 0.05, 0.05, "hierro")
    ca.cilindro(x + nx * 0.75, y + ny * 0.75, zf - 0.35, zf + 0.15, 0.15, "vidrio", "#efe2b5", lados=6, radio_arriba=0.2)
    ca.cilindro(x + nx * 0.75, y + ny * 0.75, zf + 0.15, zf + 0.35, 0.25, "hierro", lados=6, radio_arriba=0.03)
ca.objeto(col)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=())
detallar(col, m)
exportar(AGENTE, MANZANA)
p = ((l["a"][0] + l["b"][0]) / 2, (l["a"][1] + l["b"][1]) / 2)
z = altura_suelo(*p)
revisar(AGENTE, MANZANA, fotos=["IMG_20261105_130208.jpg"] if "--todas" not in sys.argv else None,
        camaras_extra=[("frente", (p[0] + l["normal"][0] * 9, p[1] + l["normal"][1] * 9, z + 1.7), (p[0], p[1], z + 4.5)),
                       ("aerea", (p[0] + l["normal"][0] * 40, p[1] + l["normal"][1] * 40, z + 35), (p[0], p[1], z))])
