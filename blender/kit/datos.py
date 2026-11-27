"""Datos del reparto: manzanas, edificios, fotos, calles y terreno. Verifica que el agente sea el dueño."""

import json
import math
import os

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AGENTES = ("claude", "codex")

_cache = {}


def _json(rel):
    if rel not in _cache:
        with open(os.path.join(RAIZ, rel)) as fh:
            _cache[rel] = json.load(fh)
    return _cache[rel]


def reparto():
    return _json("reparto/manzanas.json")


def manzana(mid):
    """Manzana (M###) o espacio público (P##, BASE) del reparto.

    Las huellas de los edificios vienen YA RECORTADAS al ancho real de las calles (ver calles_reales()); la huella
    original del lienzo queda en e["huella_lienzo"]. Los edificios que caían enteros en la calle no aparecen.
    """
    for m in reparto()["manzanas"] + reparto().get("espacios", []):
        if m["id"] == mid:
            if "_recortada" not in m:
                eds = []
                for e in m.get("edificios", []):
                    e.setdefault("huella_lienzo", e["huella"])
                    h = recortar_a_calles(e["huella_lienzo"])
                    if h:
                        e["huella"] = h
                        eds.append(e)
                m["edificios"] = eds
                m["_recortada"] = True
            return m
    raise KeyError(f"No existe la manzana o espacio {mid}")


def verificar_dueno(agente, mid):
    """Corta la ejecución si el agente no es dueño de la manzana. Llamar SIEMPRE al empezar."""
    if agente not in AGENTES:
        raise SystemExit(f"Agente desconocido {agente!r}; usa uno de {AGENTES}")
    m = manzana(mid)
    if m["dueno"] != agente:
        raise SystemExit(f"{mid} es de {m['dueno']}, no de {agente}. No la modeles. Ver reparto/manzanas.json")
    return m


def edificio(mid, eid):
    for e in manzana(mid)["edificios"]:
        if e["id"] == eid:
            return e
    raise KeyError(f"{eid} no está en {mid}")


def ubicaciones():
    return _json("fotos/ubicaciones.json")["fotos"]


def gps_camara(archivo):
    """(x, y) donde estaba el CELULAR según el EXIF (aprox., error de 5–20 m), o None.

    Ojo: es la posición de la cámara, no del objeto. El objeto está en ubicaciones()[archivo].
    """
    for f in _json("web/public/fotos/indice.json"):
        if f["archivo"] == archivo and f["gps"]:
            return f["gps"]["x"], f["gps"]["y"]
    return None


def ruta_foto(archivo, tamano="medio"):
    """tamano: 'medio' (1600 px, para mirar) u 'original' (4000 px, para detalles finos)."""
    if tamano == "original":
        return os.path.join(RAIZ, "fotos", archivo)
    return os.path.join(RAIZ, "web", "public", "fotos", tamano, os.path.splitext(archivo)[0] + ".jpg")


def calles():
    return _json("web/public/mapa/calles.json")


# --------------------------------------------------------------------------- ancho real de las calles


def calles_reales():
    """Calles con ancho real (reparto/calles_reales.json): nombre, ancho (fachada a fachada), vereda, eje [[x, y]…]."""
    try:
        return _json("reparto/calles_reales.json")["calles"]
    except FileNotFoundError:
        return []


def _area(h):
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(h, h[1:] + h[:1])) / 2


def _cortar_semiplano(h, ax, ay, nx, ny, dmin):
    """Deja la parte de h con (p - a)·n >= dmin (Sutherland–Hodgman con un semiplano)."""
    f = lambda p: (p[0] - ax) * nx + (p[1] - ay) * ny - dmin
    res = []
    for p, q in zip(h, h[1:] + h[:1]):
        fp, fq = f(p), f(q)
        if fp >= 0:
            res.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            res.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return res


def recortar_a_calles(huella, area_min=6.0):
    """Huella recortada para que ninguna parte quede dentro del corredor real de una calle (None si no queda nada)."""
    clave = ("recorte", tuple(map(tuple, huella)))
    if clave in _cache:
        return _cache[clave]
    h = [tuple(p) for p in huella]
    for c in calles_reales():
        if not c.get("recortar", True):
            continue
        w = c["ancho"] / 2
        eje = c["eje"]
        for a, b in zip(eje, eje[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            L = math.hypot(dx, dy)
            if L < 0.3 or len(h) < 3:
                continue
            ux, uy = dx / L, dy / L
            nx, ny = -uy, ux
            # ¿algún vértice o lado de la huella entra en el corredor de este tramo?
            invade, lado = False, 0.0
            for p, q in zip(h, h[1:] + h[:1]):
                for k in range(5):
                    x, y = p[0] + (q[0] - p[0]) * k / 4, p[1] + (q[1] - p[1]) * k / 4
                    t = (x - a[0]) * ux + (y - a[1]) * uy
                    d = (x - a[0]) * nx + (y - a[1]) * ny
                    lado += d
                    if -0.2 <= t <= L + 0.2 and abs(d) < w - 0.05:
                        invade = True
            if not invade:
                continue
            sg = 1.0 if lado >= 0 else -1.0
            h = _cortar_semiplano(h, a[0], a[1], nx * sg, ny * sg, w)
    # limpiar puntos repetidos
    lim = []
    for p in h:
        if not lim or math.hypot(p[0] - lim[-1][0], p[1] - lim[-1][1]) > 0.05:
            lim.append((round(p[0], 3), round(p[1], 3)))
    if len(lim) > 2 and math.hypot(lim[0][0] - lim[-1][0], lim[0][1] - lim[-1][1]) <= 0.05:
        lim.pop()
    res = [list(p) for p in lim] if len(lim) >= 3 and abs(_area(lim)) >= area_min else None
    _cache[clave] = res
    return res


def edificios_recortados():
    """Huellas de TODOS los edificios del lienzo de la zona, recortadas a las calles reales."""
    if "_edif_rec" not in _cache:
        _cache["_edif_rec"] = [h for h in (recortar_a_calles(e["huella"]) for e in _json("reparto/edificios_lienzo.json")) if h]
    return _cache["_edif_rec"]


def calle_real_cercana(x, y):
    """(distancia al eje, ancho, vereda, nombre) de la calle real más próxima, o None si no hay datos."""
    mejor = None
    for c in calles_reales():
        for a, b in zip(c["eje"], c["eje"][1:]):
            d, _ = _dist_seg(x, y, a, b)
            if mejor is None or d < mejor[0]:
                mejor = (d, c["ancho"], c["vereda"], c["nombre"])
    return mejor


def altura_suelo(x, y):
    """Altura del terreno del lienzo en (x, y), interpolada de reparto/terreno.json (rejilla de 5 m)."""
    t = _json("reparto/terreno.json")
    ox, oy = t["origen"]
    p, n, z = t["paso"], t["n"], t["z"]
    fx, fy = (x - ox) / p, (y - oy) / p
    i, j = max(0, min(n - 2, int(fx))), max(0, min(n - 2, int(fy)))
    u, v = fx - i, fy - j
    return (z[j][i] * (1 - u) * (1 - v) + z[j][i + 1] * u * (1 - v) + z[j + 1][i] * (1 - u) * v + z[j + 1][i + 1] * u * v)


def _dist_seg(px, py, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    l2 = dx * dx + dy * dy or 1
    t = max(0, min(1, ((px - a[0]) * dx + (py - a[1]) * dy) / l2))
    return math.hypot(px - a[0] - t * dx, py - a[1] - t * dy), (a[0] + t * dx, a[1] + t * dy)


def calle_cercana(x, y, con_nombre=True):
    """(distancia, punto_más_cercano, nombre) de la calle más próxima."""
    mejor = (1e9, None, "")
    for c in calles():
        if con_nombre and not c["nombre"]:
            continue
        if c["tipo"] in ("footway", "steps", "path"):
            continue
        for a, b in zip(c["puntos"], c["puntos"][1:]):
            d, q = _dist_seg(x, y, a, b)
            if d < mejor[0]:
                mejor = (d, q, c["nombre"])
    return mejor


def orientar_ccw(huella):
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(huella, huella[1:] + huella[:1]))
    return huella if area > 0 else list(reversed(huella))


def lados(huella):
    """Lados de la huella (CCW) con su largo, normal hacia afuera y si dan a la calle.

    Un lado da a la calle si, al salir 3 m hacia afuera desde su centro, se queda cerca del eje de una calle
    (a menos de medio ancho real + 3,5 m, o de 9 m si la calle no tiene ancho real) y no se cae dentro de otro
    edificio (huellas ya recortadas a las calles reales).
    """
    h = orientar_ccw([tuple(p) for p in huella])
    otros = edificios_recortados()
    res = []
    for i, (a, b) in enumerate(zip(h, h[1:] + h[:1])):
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 0.3:
            continue
        nx, ny = dy / L, -dx / L
        mx, my = (a[0] + b[0]) / 2 + nx * 3, (a[1] + b[1]) / 2 + ny * 3
        d, _, nombre = calle_cercana(mx, my, con_nombre=False)
        cerca = d < 9
        real = calle_real_cercana(mx, my)
        if real and real[0] < real[1] / 2 + 3.5:
            cerca, nombre = True, real[3]
        tapado = any(_dentro(mx, my, o) for o in otros)
        res.append({"i": i, "a": a, "b": b, "largo": round(L, 2), "normal": (nx, ny),
                    "a_calle": cerca and not tapado, "calle": nombre if cerca else ""})
    return res


def dentro_de_edificio(x, y):
    return any(_dentro(x, y, h) for h in edificios_recortados())


def _dentro(px, py, pts):
    r = False
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        if (y0 > py) != (y1 > py) and px < x0 + (py - y0) * (x1 - x0) / (y1 - y0):
            r = not r
    return r
