"""M033 — esquina Calle Aniceto Arce × Calle Fray José Antonio de San Alberto (continuación de Ravelo al SE de Arce).

Fotos 125952…130052 (todas desde el cruce Ravelo/Arce): E54bc4f es el edificio de ESQUINA REDONDEADA
(años 40): planta baja revestida de piedra gris con tiendas, 1.º y 2.º piso con ventanas corridas en franja
separadas por bandas blancas, 3.er piso retranqueado con ventanas y alero de tejas. ~13.5 m. (#2 #3 #6 #7)
Resto (Hotel Premier E65a78f, Las Torres E7d65de, E05f69a sobre Arce): sin foto directa → casas sencillas de
2–3 plantas. Interiores sin foto.
"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kit import *  # noqa: E402,F403
from kit.datos import orientar_ccw  # noqa: E402
from piezas_claude import adelantada, cortina_metalica, lado_lienzo, casa_sencilla, fachada, lado_virtual, suelo_huella, tejado_dos_aguas  # noqa: E402

AGENTE = "claude"
MANZANA = "M033"
m, col = iniciar(AGENTE, MANZANA)
E = {e["id"]: e for e in m["edificios"]}
BLANCO = "#f3f3ef"
PIEDRA_GRIS = "#8e8f86"

# =========================================================================== E54bc4f: esquina redondeada
h = orientar_ccw([tuple(p) for p in E["E54bc4f"]["huella"]])
ls = {l["i"]: lado_lienzo(E["E54bc4f"], l["i"]) for l in lados(E["E54bc4f"]["huella_lienzo"])}
esq = ls[0]["a"]                      # vértice entre lado 3 (San Alberto) y lado 0 (Arce)
k0 = min(range(len(h)), key=lambda i: math.hypot(h[i][0] - esq[0], h[i][1] - esq[1]))
prev, nxt = h[k0 - 1], h[(k0 + 1) % len(h)]
R = 4.5


def hacia(p, q, d):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    return (p[0] + (q[0] - p[0]) * d / L, p[1] + (q[1] - p[1]) * d / L)


a0, a1 = hacia(esq, prev, R), hacia(esq, nxt, R)
curva = []
for j in range(9):  # bezier cuadrática con el vértice como control
    t = j / 8
    curva.append(((1 - t) ** 2 * a0[0] + 2 * (1 - t) * t * esq[0] + t * t * a1[0],
                  (1 - t) ** 2 * a0[1] + 2 * (1 - t) * t * esq[1] + t * t * a1[1]))
h2 = h[:k0] + curva + h[k0 + 1:]

c = Constructor("E54bc4f")
zb, zr = suelo_huella(h2)
ALTO, RETIRO = 10.6, 1.2
import random  # noqa: E402
rnd33 = random.Random("M033-pb")
c.prisma(h2, zb - 0.6, zr + ALTO, "muro", BLANCO, tapa=False)
techo_plano(c, h2, zr + ALTO + 3.2 - 0.02)
# tramos de fachada a la calle: recto San Alberto, curva, recto Arce
tramos = [(prev, a0)] + list(zip(curva, curva[1:])) + [(a1, nxt)]
# y los demás lados a la calle de la huella recortada (recorrido a pie: el tramo de Arce más allá del primer vértice
# quedaba como muro liso de 14 m)
_hechos = {(round(p[0], 2), round(p[1], 2)) for p, _ in tramos}
for _l in lados(h2):
    if _l["a_calle"] and _l["largo"] > 2.0 and (round(_l["a"][0], 2), round(_l["a"][1], 2)) not in _hechos:
        tramos.append((tuple(_l["a"]), tuple(_l["b"])))
for p, q in tramos:
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    n = ((q[1] - p[1]) / L, -(q[0] - p[0]) / L)
    f = fachada(c, lado_virtual(p, q, n))
    off = zr - f.suelo
    f.caja(0.0, L, zb - 0.6 - f.suelo, 3.6 + off, 0.0, 0.08, "zocalo_piedra", PIEDRA_GRIS)       # planta baja
    # planta baja (fotos #2 #6 y recorrido a pie): pilares de piedra con llagas, vitrinas con marco y montante,
    # alguna cortina metálica y letreros de los locales (antes era un paño de vidrio de 3 m que a pie se leía liso)
    hl = 0.55
    while hl < 3.5 + off:
        f.caja(0.0, L, hl, hl + 0.025, 0.08, 0.095, "moldura", "#6f706a")
        hl += 0.55
    if L > 3:
        nb = max(1, round(L / 3.6))
        bw = L / nb
        for j in range(nb):
            s0, s1 = j * bw + 0.3, (j + 1) * bw - 0.3
            sm = (s0 + s1) / 2
            tipo = rnd33.random()
            if tipo < 0.25:
                cortina_metalica(adelantada(f, 0.085), sm, ancho=s1 - s0, alto=2.75 + off, h0=0.0)
            else:
                f.caja(s0, s1, 0.0, 2.75 + off, 0.06, 0.1, "marco_ventana", "#3b3f42")
                f.caja(s0 + 0.08, s1 - 0.08, 0.45, 2.3 + off, 0.1, 0.11, "vidrio")
                f.caja(s0 + 0.08, s1 - 0.08, 2.38 + off, 2.68 + off, 0.1, 0.11, "vidrio")     # montante
                f.caja(s0, s1, 2.3 + off, 2.38 + off, 0.06, 0.13, "marco_ventana", "#3b3f42")
                if tipo > 0.6:                                                        # puerta vidriada
                    f.caja(sm - 0.5, sm - 0.45, 0.0, 2.3 + off, 0.1, 0.14, "marco_ventana", "#3b3f42")
                    f.caja(sm + 0.45, sm + 0.5, 0.0, 2.3 + off, 0.1, 0.14, "marco_ventana", "#3b3f42")
            if rnd33.random() < 0.6:                                                  # letrero del local
                f.caja(s0 + 0.2, s1 - 0.2, 2.95 + off, 3.45 + off, 0.08, 0.16, "letrero",
                       rnd33.choice(["#f2efe6", "#c94f3d", "#2f5e8e", "#e8b23a", "#f2efe6"]))
    f.caja(-0.02, L + 0.02, 3.6 + off, 3.9 + off, 0.0, 0.35, "moldura", BLANCO)                 # marquesina
    for piso in (0, 1):                                                                          # franjas
        hb = 3.9 + piso * 3.35 + off
        f.caja(0.0, L, hb + 0.95, hb + 2.6, 0.0, 0.03, "vidrio")
        kk = 0.0
        while kk <= L + 0.01:
            f.caja(kk - 0.04, kk + 0.04, hb + 0.95, hb + 2.6, 0.0, 0.06, "marco_ventana", "#e9ecef")
            kk += max(L / max(1, round(L / 1.2)), 0.5)
        f.caja(-0.02, L + 0.02, hb + 2.6, hb + 2.85, 0.0, 0.12, "moldura", BLANCO)
    # último piso retranqueado con alero
    f.caja(0.0, L, ALTO + off, ALTO + 0.25 + off, 0.0, 0.15, "moldura", BLANCO)
    f.caja(0.0, L, ALTO + off, ALTO + 3.2 + off, -RETIRO - 0.3, -RETIRO, "muro", BLANCO)
    if L > 2.5:
        f.caja(0.5, L - 0.5, ALTO + 0.9 + off, ALTO + 2.3 + off, -RETIRO, -RETIRO + 0.02, "vidrio")
    alero_tejas(f, ALTO + 3.1 + off, vuelo=0.7, fondo=1.5, canes=False, s0=-0.05, s1=L + 0.05)
# el piso retranqueado se cierra también en las medianeras (R0126: "de este lado no tiene pared"): muro desde la
# cornisa hasta el techo en cada lado que no da a la calle
for _l in lados(h2):
    if _l["a_calle"] and _l["largo"] > 2.0:
        continue
    (ax_, ay_), (bx_, by_) = _l["a"], _l["b"]
    nx_, ny_ = _l["normal"]
    z0_, z1_ = zr + ALTO - 0.05, zr + ALTO + 3.2
    c.poligono([(ax_, ay_, z0_), (bx_, by_, z0_), (bx_, by_, z1_), (ax_, ay_, z1_)], "muro", BLANCO, grosor=0.25,
               normal_extrusion=(-nx_ * 0.25, -ny_ * 0.25, 0.0))
c.objeto(col)

# =========================================================================== resto con frente a calle (sin foto)
CALLES = ("Calle Fray José Antonio de San Alberto", "Calle Aniceto Arce")
for eid, pisos in (("E65a78f", 3), ("E7d65de", 3), ("E05f69a", 2)):
    e = E[eid]
    c = Constructor(eid)
    zb, zr = suelo_huella(e["huella"])
    alto = pisos * 3.7
    c.prisma(e["huella"], zb - 0.6, zr + alto, "muro", "#f4f1ea", tapa=False)
    techo_plano(c, e["huella"], zr + alto - 0.02)
    for l in lados(e["huella"]):
        if l["a_calle"] and l["calle"] in CALLES and l["largo"] > 4:
            f = fachada(c, l)
            n = max(1, round(l["largo"] / 3.6))
            vanos = [l["largo"] * (k + 0.5) / n for k in range(n)]
            casa_sencilla(f, 0.0, l["largo"], pisos, 3.7, zr - f.suelo, muro=("muro", "#f4f1ea"), vanos=vanos,
                          balcones=vanos[::2], puertas=vanos[::3], desde=zb - 0.6 - f.suelo)
    c.objeto(col)

for eid, e in E.items():
    if eid in ("E54bc4f", "E65a78f", "E7d65de", "E05f69a"):
        continue
    c = Constructor(eid)
    zb, zt = suelo_huella(e["huella"])
    alto = 6.5 if e["area_m2"] > 40 else 4.5
    c.prisma(e["huella"], zb - 0.6, zt + alto, "muro", "#efe8dc")
    tejado_dos_aguas(c, e["huella"], zt + alto, pendiente=24)
    c.objeto(col)


# =========================================================================== FRENTE SE DE ARCE sin huellas del lienzo
# (sección Arce, 2026-11-14, R0124/R0125): entre E05f69a y M041 la vereda daba a un lote vacío que el relleno
# llenaba de casas sueltas ("ciudad perdida"). Sin fotos de este frente: hilera continua de casas del centro
# diseñada para esta cuadra (2–3 plantas, blancas y cremas, una con pretil de remates), solo el cuerpo que da a la
# calle, hasta la primera huella de atrás. t = metros sobre el eje de Arce desde Ravelo (frente_calle.py).
from piezas_claude import casas_de_frente, tramo_calle  # noqa: E402
ARCE = tramo_calle("Calle Aniceto Arce", (-150.0, -70.0))
casas_de_frente(col, "M033_arce_a", ARCE, +1, [
    (8.3, 2, 4.2, "#f6f4ef", "alero", dict(vanos=[1.5, 4.15, 6.8], puertas=[4.15], balcones=[1.5, 6.8])),
    (7.0, 2, 4.0, "#f1e6cf", "cornisa", dict(vanos=[1.6, 3.5, 5.4], puertas=[1.6], balcones=[3.5])),
    (9.5, 3, 3.6, "#f6f4ef", "pinaculos", dict(vanos=[1.4, 3.6, 5.9, 8.1], puertas=[3.6],
                                               balcones=[1.4, 3.6, 5.9, 8.1], acento="#d4ab5c")),
    (6.5, 2, 4.2, "#efe3c4", "alero", dict(vanos=[1.6, 4.9], puertas=[4.9], balcones=[1.6], comercio=False)),
    (8.0, 2, 4.4, "#f4efe4", "cornisa", dict(vanos=[1.4, 4.0, 6.6], puertas=[1.4, 6.6], balcones=[4.0])),
], t0=43.5)
casas_de_frente(col, "M033_arce_b", ARCE, +1, [
    (7.6, 2, 4.2, "#f6f4ef", "alero", dict(vanos=[1.5, 3.8, 6.1], puertas=[3.8], balcones=[1.5, 6.1])),
    (6.5, 2, 4.0, "#eef0f1", "cornisa", dict(vanos=[1.6, 4.9], puertas=[1.6], balcones=[4.9])),
], t0=92.0)

from detalles_claude import detallar, relleno_manzana, techos_con_patio  # noqa: E402
relleno_manzana(col, m)
techos_con_patio(col, excluir=("E54bc4f",))
detallar(col, m)
from vecinos_claude import preparar  # noqa: E402
preparar(col, MANZANA)      # recorte contra el muro del vecino (SIAMESES) ahora que el relieve de fachada ya no se aplana
exportar(AGENTE, MANZANA)
z = altura_suelo(*esq)
d = (esq[0] - (prev[0] + nxt[0]) / 2, esq[1] - (prev[1] + nxt[1]) / 2)
dl = math.hypot(*d)
revisar(AGENTE, MANZANA, fotos=["IMG_20261105_130051.jpg"] if "--todas" not in sys.argv else None,
        camaras_extra=[("esquina", (esq[0] + d[0] / dl * 16, esq[1] + d[1] / dl * 16, z + 1.7), (esq[0], esq[1], z + 6)),
                       ("aerea", (esq[0] + d[0] / dl * 45, esq[1] + d[1] / dl * 45, z + 40), (*m["centro"], z))])
