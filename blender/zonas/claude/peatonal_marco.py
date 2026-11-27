"""Marco de la PEATONAL de Junín (Calle Batalla de Junín entre Ravelo y la Av. Hernando Siles), 2026-11-13.

El eje es recto (reparto/calles_reales.json, tramo con "peatonal": true) y la sección es asimétrica: vereda NO 3,5 m,
calzada de adoquín 5 m, vereda SE 6 m ("las aceras son muy anchas, sobre todo la derecha", usuario).

  s: metros a lo largo del eje desde su extremo SO (lado Ravelo) hacia Hernando Siles.
  lado "NO" / "SE": cada frente de la calle. d: metros desde la línea de fachada hacia ADENTRO de la manzana
  (negativo = sobre la vereda).

FONDO: profundidad de la franja de edificios que construye PEATONAL.py; las manzanas vecinas (M011, M012, M004,
M013, AMP_NO) recortan sus huellas con `cortar_franja` para no superponerse.
"""

import math

from kit.datos import calles_reales

_J = [c for c in calles_reales() if c.get("peatonal")][0]
A, B = tuple(_J["eje"][0]), tuple(_J["eje"][-1])
LARGO = math.hypot(B[0] - A[0], B[1] - A[1])
U = ((B[0] - A[0]) / LARGO, (B[1] - A[1]) / LARGO)
NL = (-U[1], U[0])                      # izquierda del sentido del eje = lado NO
W = _J["ancho"] / 2
VEREDA = {"NO": _J.get("vereda_izq", _J["vereda"]), "SE": _J.get("vereda_der", _J["vereda"])}
SG = {"NO": 1.0, "SE": -1.0}
FONDO = {"NO": 14.0, "SE": 14.0}


def P(lado, s, d=0.0):
    """Punto de la línea de fachada del lado (d > 0 hacia adentro de la manzana, d < 0 sobre la vereda)."""
    k = SG[lado] * (W + d)
    return (A[0] + U[0] * s + NL[0] * k, A[1] + U[1] * s + NL[1] * k)


def NOUT(lado):
    """Normal de la fachada hacia la calle."""
    return (-NL[0] * SG[lado], -NL[1] * SG[lado])


def sd(x, y):
    """(s, distancia con signo a la izquierda del eje) de un punto."""
    dx, dy = x - A[0], y - A[1]
    return dx * U[0] + dy * U[1], dx * NL[0] + dy * NL[1]


def _en_otra_calle(x, y, margen=0.0):
    for c in calles_reales():
        if c is _J or c.get("peatonal"):
            continue
        if c["nombre"] == _J["nombre"]:
            continue
        w = c["ancho"] / 2 + margen
        for a, b in zip(c["eje"], c["eje"][1:]):
            ex, ey = b[0] - a[0], b[1] - a[1]
            L2 = ex * ex + ey * ey or 1
            t = ((x - a[0]) * ex + (y - a[1]) * ey) / L2
            if -0.02 <= t <= 1.02 and math.hypot(x - a[0] - t * ex, y - a[1] - t * ey) < w:
                return True
    return False


def limites(lado):
    """(s_ini, s_fin) de la línea de fachada del lado, entre los corredores de Ravelo y de Hernando Siles."""
    ss = [s * 0.25 for s in range(int(LARGO * 4))]
    libres = [s for s in ss if not _en_otra_calle(*P(lado, s, 0.3))]
    # el tramo continuo más largo
    mejor, ini, prev = (0, 0, 0), None, None
    for s in libres:
        if prev is None or s - prev > 0.3:
            ini = s
        prev = s
        if s - ini > mejor[0]:
            mejor = (s - ini, ini, s)
    return mejor[1], mejor[2]


def en_franja(x, y, lado=None, margen=0.0):
    s, dd = sd(x, y)
    if not (-12.0 <= s <= LARGO + 12.0):
        return False
    for l in ([lado] if lado else ("NO", "SE")):
        k = dd * SG[l]
        if k <= W + FONDO[l] + margen:
            return True
    return False


def cortar_franja(h, lado):
    """Deja la parte de la huella h que queda DETRÁS de la franja de PEATONAL del lado (o None si no queda nada)."""
    from kit.datos import _cortar_semiplano
    n = (NL[0] * SG[lado], NL[1] * SG[lado])
    r = _cortar_semiplano([tuple(p) for p in h], A[0], A[1], n[0], n[1], W + FONDO[lado])
    return r if len(r) >= 3 else None
