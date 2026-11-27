"""M011 — frente a Ravelo, al NO de la esquina con Junín (frente a M009).
Correcciones R0077/R0078 (2026-11-13): la esquina es "un punto muy reconocible de la ciudad": casona blanca colonial
de 2 plantas con alero de tejas y canes, gran MIRADOR de madera oscura en la esquina con el letrero "Feria de
Libros", molduras sobre las ventanas altas, balcones de hierro, zócalo de piedra y locales (libros, telefonía).

Una sola foto (130233, desde la esquina Ravelo × Junín): casa blanca de 2 plantas con techo de tejas y un gran
mirador de madera en el 1.er piso sobre la esquina (Ea81c1b, lados 3 y 4). Resto: versión sencilla (generica.py).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generica import construir  # noqa: E402
from kit import Constructor, lados  # noqa: E402
from piezas_claude import lado_lienzo, fachada, mirador, suelo_huella  # noqa: E402


def mirador_esquina(m, col):
    e = [x for x in m["edificios"] if x["id"] == "Ea81c1b"][0]
    zb, zr = suelo_huella(e["huella"])
    c = Constructor("Ea81c1b_mirador")
    l4 = lado_lienzo(e, 4)
    f = fachada(c, l4)
    off = zr - f.suelo
    mirador(f, 2.4, 4.6 + off, ancho=4.2, alto=2.7, vuelo=1.1, base=("madera", "#5a3322"),
            madera=("marco_ventana", "#5a3322"), antepecho=("madera", "#6b3a26"))
    c.objeto(col)
    # (2026-11-13) la casona de la esquina con Junín y su mirador los construye PEATONAL.py


def mirador_junin(m, col):
    """Casona de la esquina Junín × Ravelo (R0077, R0078): gran mirador de madera oscura en la punta de la fachada a
    Junín, con el letrero "Feria de Libros"; vitrinas de libros abajo."""
    import math as _m
    from piezas_claude import lado_virtual
    ESQ = (-215.1, 66.7)
    # la casona de frente en las fotos es E0d8704 (rayo desde la cámara de R0077); el mirador va en la punta de su
    # fachada a Junín más cercana a la esquina con Ravelo
    e = [x for x in m["edificios"] if x["id"] == "E0d8704"][0]
    h = e["huella"]
    i = min(range(len(h)), key=lambda k: _m.hypot(h[k][0] - ESQ[0], h[k][1] - ESQ[1]))
    cand = []
    for k in (i - 1, i):
        a, b = h[k % len(h)], h[(k + 1) % len(h)]
        L = _m.hypot(b[0] - a[0], b[1] - a[1])
        if L < 3:
            continue
        n = ((b[1] - a[1]) / L, -(b[0] - a[0]) / L)
        cand.append((n[0] * 0.76 + n[1] * -0.65, a, b, n))
    sc, a, b, n = max(cand, key=lambda x: abs(x[0]))
    if sc < 0:
        n = (-n[0], -n[1])
    if _m.hypot(b[0] - ESQ[0], b[1] - ESQ[1]) < _m.hypot(a[0] - ESQ[0], a[1] - ESQ[1]):
        a, b = b, a
    zb, zr = suelo_huella(h)
    c = Constructor(e["id"] + "_mirador_junin")
    f = fachada(c, lado_virtual(a, b, n))
    off = zr - f.suelo
    print("[M011] mirador Junín × Ravelo en", e["id"], tuple(round(v, 1) for v in a))
    mirador(f, 2.4, 4.6 + off, ancho=4.4, alto=2.8, vuelo=1.15, base=("madera", "#5a3322"),
            madera=("marco_ventana", "#5a3322"), antepecho=("madera", "#6b3a26"))
    for k in range(7):
        f.caja(0.9 + k * 0.46, 1.17 + k * 0.46, 6.0 + off, 6.6 + off, 1.09, 1.11, "letrero", "#2f55a8")
    for s_ in (5.6, 7.0):
        f.caja(s_ - 0.6, s_ + 0.6, 0.0, 2.0 + off, 0.15, 0.45, "letrero", "#c9b28a")
        for hh in (0.3, 0.75, 1.2, 1.65):
            f.caja(s_ - 0.55, s_ + 0.55, hh + off, hh + 0.35 + off, 0.46, 0.48, "letrero", "#8a6a9a" if int(hh * 10) % 2 else "#b9694f")
    c.objeto(col)


from peatonal_marco import cortar_franja, sd  # noqa: E402


def _filtro(e):
    """Lo que cae en la franja de PEATONAL (lado NO, desde Ravelo) se quita; el resto queda."""
    if all(sd(*p)[0] < -6.0 for p in e["huella"]):
        return e["huella"]
    return cortar_franja(e["huella"], "NO")


construir("claude", "M011", extra=mirador_esquina, filtro_huella=_filtro,
          forzar={"E0d8704": {"tipo": "colonial", "muro": "#f6f4ef", "pisos": 2},
                  "E0d20b6": {"tipo": "colonial", "muro": "#f6f4ef", "pisos": 2}})
