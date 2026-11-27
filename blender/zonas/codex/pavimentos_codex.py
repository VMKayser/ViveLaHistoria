"""Pavimentos junto a ejes curvos: diferencia con corredores FINITOS.

El recorte por semiplanos de toda una huella prolongaba cada tangente de
la calle y quitaba cuñas de hasta tres metros dentro de P01 (#23).
Cada triángulo se parte contra el rectángulo de cada tramo real; se
conservan todas las piezas exteriores, sin prolongar la tangente.
"""
import math
from triangulacion_codex import triangular_huella


def _partir(h, distancia):
    dentro, fuera = [], []
    for p, q in zip(h, h[1:] + h[:1]):
        dp, dq = distancia(p), distancia(q)
        (dentro if dp >= 0 else fuera).append(p)
        if (dp >= 0) != (dq >= 0):
            t = dp / (dp - dq)
            r = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))
            dentro.append(r)
            fuera.append(r)
    return dentro, fuera


def _area(h):
    return abs(sum(p[0]*q[1]-p[1]*q[0] for p,q in zip(h,h[1:]+h[:1]))) / 2


def pavimento_fuera_calles(huella, calles, hasta_calzada=False):
    """Polígonos convexos de la plaza hasta la vereda real, sin calzada.

    Se solapan 50 cm por debajo de la vereda de BASE para cerrar costuras. Se usan
    tapas de 3 cm para absorber el redondeo de vértices al exportar GLB.
    """
    piezas = [list(t) for t in triangular_huella(huella)]
    for calle in calles:
        w = (calle['ancho']/2-calle['vereda']+.005 if hasta_calzada
             else calle['ancho']/2-min(.5,calle['vereda']/2))
        for a, b in zip(calle['eje'], calle['eje'][1:]):
            dx, dy = b[0]-a[0], b[1]-a[1]
            largo = math.hypot(dx, dy)
            if largo < .05:
                continue
            ux, uy = dx/largo, dy/largo
            def s(p): return (p[0]-a[0])*ux + (p[1]-a[1])*uy
            def d(p): return -(p[0]-a[0])*uy + (p[1]-a[1])*ux
            nuevas = []
            for h in piezas:
                ss, dd = [s(p) for p in h], [d(p) for p in h]
                if max(ss) <= -.03 or min(ss) >= largo+.03 or min(dd) >= w or max(dd) <= -w:
                    nuevas.append(h)
                    continue
                # Diferencia con un convexo: emitir el exterior de cada
                # semiplano y seguir recortando solo su parte interior.
                resto = h
                for distancia in (lambda p:s(p)+.03, lambda p:largo+.03-s(p),
                                  lambda p:w-d(p), lambda p:w+d(p)):
                    if len(resto) < 3:
                        break
                    resto, exterior = _partir(resto, distancia)
                    if len(exterior) >= 3 and _area(exterior) > 1e-8:
                        nuevas.append(exterior)
            piezas = nuevas
    return piezas
