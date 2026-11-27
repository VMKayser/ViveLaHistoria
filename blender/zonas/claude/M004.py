"""M004 — frente NO de Junín entre la casona de M012 y el edificio moderno de AMP_NO (correcciones R0074, R0075).

"Shopping Florencia" (t ≈ 40–49 sobre el eje de Junín): edificio angosto de 4 plantas con REMATE EN PUNTA (marco
triangular blanco), dos calles de ventanales verticales de madera marrón que suben tres plantas, balcón central con
balaustrada blanca y el letrero del shopping, tejadillos de teja oscura arriba, y locales abajo (servicio técnico,
vidrieras). Las huellas del lienzo de M004 caen todas en este frente: se reemplazan por el edificio.
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generica import construir  # noqa: E402
from kit import arquitectura as A  # noqa: E402
import junin_norte as JN  # noqa: E402
from mercado_claude import tienda  # noqa: E402

JN._cen = (-200.0, 160.0)   # lado NO de Junín


def florencia(m, col):
    rnd = random.Random("florencia")
    c, f, off = JN.cuerpo("M004_shopping_florencia", 38.2, 51.2, 14.0, 14.6, color="#f3f0e8")
    L = f.largo
    print("[M004] Florencia: frente", round(L, 2), "m, desde", tuple(round(v, 1) for v in f.a))
    MAR = "#6b4430"
    for s0 in (0.4, 2.7, L - 4.7, L - 2.4):                   # ventanales verticales de madera, 3 plantas
        f.caja(s0, s0 + 2.0, 4.4 + off, 13.4 + off, 0.0, 0.35, "marco_ventana", MAR)
        f.caja(s0 + 0.12, s0 + 1.88, 4.6 + off, 13.2 + off, 0.36, 0.37, "vidrio")
        for h in (6.0, 7.6, 9.2, 10.8, 12.4):
            f.caja(s0, s0 + 2.0, h + off, h + 0.08 + off, 0.3, 0.42, "marco_ventana", MAR)
        f.caja(s0 + 0.96, s0 + 1.04, 4.4 + off, 13.4 + off, 0.3, 0.42, "marco_ventana", MAR)
        f.caja(s0 - 0.15, s0 + 2.15, 13.4 + off, 13.75 + off, -0.1, 0.55, "teja", "#8a4a32")    # tejadillo
    sm = L / 2
    # balcón central con balaustrada blanca y el letrero del shopping, ventana encima
    f.caja(sm - 1.5, sm + 1.5, 4.4 + off, 4.6 + off, 0.0, 0.8, "piedra", "#f3f0e8")
    k = sm - 1.4
    while k < sm + 1.4:
        f.cilindro_vertical(k, 4.6 + off, 5.4 + off, 0.65, 0.05, "moldura", "#f6f4ef", lados=6)
        k += 0.2
    f.caja(sm - 1.5, sm + 1.5, 5.4 + off, 5.5 + off, 0.55, 0.82, "moldura", "#f6f4ef")
    f.caja(sm - 1.3, sm + 1.3, 4.0 + off, 4.4 + off, 0.8, 0.84, "letrero", "#7a4a2e")         # SHOPPING FLORENCIA
    for h in (5.8, 8.8):
        A.ventana(f, sm, h + off, ancho=1.3, alto=2.0, moldura="moldura", color_moldura="#f6f4ef",
                  carpinteria="marco_ventana", color_carpinteria=MAR)
    f.caja(sm - 1.6, sm + 1.6, 8.5 + off, 8.65 + off, 0.0, 0.7, "moldura", "#f6f4ef")
    # remate en punta: marco triangular blanco sobre la calle central
    p = [f.punto(sm - 1.7, 14.6 + off, 0.2), f.punto(sm + 1.7, 14.6 + off, 0.2), f.punto(sm, 16.6 + off, 0.2)]
    f.c.poligono(p, "moldura", "#f6f4ef", grosor=0.3, normal_extrusion=tuple(f.n))
    f.esfera(sm, 15.3 + off, 0.55, 0.25, "madera", "#7a4a2e")
    f.caja(-0.1, L + 0.1, 14.4 + off, 14.65 + off, 0.0, 0.5, "teja", "#8a4a32")
    # planta baja: locales y letrero verde de servicio técnico
    s_ = 0.2
    while s_ + 3.0 <= L:
        tienda(f, s_, s_ + 3.0, off, rnd, toldo="#f1eee6", vuelo=1.3)
        s_ += 3.0
    f.caja(L * 0.35, L * 0.75, 3.45 + off, 3.95 + off, 1.3, 1.36, "letrero", "#2e8a5a")
    c.objeto(col)


# 2026-11-13: el frente a Junín (Shopping Florencia y vecinos) lo construye PEATONAL.py; aquí solo queda lo de atrás
from peatonal_marco import cortar_franja  # noqa: E402
construir("claude", "M004", filtro_huella=lambda e: cortar_franja(e["huella"], "NO"))
