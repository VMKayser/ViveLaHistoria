"""Calles con su ancho REAL (fachada a fachada) para toda la zona → reparto/calles_reales.json.

Por qué: las huellas del lienzo (FBX) están engordadas hacia la calle; medidas sobre las fotos y la imagen satelital,
las calles reales son 1–4 m más anchas (Ravelo ≈ 13,5 m de fachada a fachada contra ≈ 10,8 m del lienzo).

Qué hace:
- Toma el eje de cada calle con nombre de OSM (calles.json) dentro de la zona.
- Lo corre al punto medio entre las fachadas del lienzo de ambos lados (si las dos están a < 14 m), suavizado.
- Le asigna el ancho real (ANCHOS) y el ancho de vereda (VEREDAS).

El kit (datos.manzana) recorta cada huella para que ninguna fachada entre en el corredor de la calle, y la BASE
construye calzada, veredas y bordillos con estos mismos datos.

Uso: python3 scripts/calles_reales.py
"""

import json
import math
import os
from collections import defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# fachada a fachada (m). Medido en fotos (carriles + veredas) y en la imagen satelital.
# Ensanche 2026-11-13 (usuario: "calles estrechas, aceras diminutas"): +1 m de fachada a fachada en las calles comunes
# y vereda mínima de 2,2 m; la plaza, la Peatonal y Hernando Siles conservan sus medidas.
ANCHOS = {
    # Ravelo y Arce (solo manzanas de claude en las dos veredas): +1,5 m más, veredas de 3 m y 2,8 m (correcciones
    # R0125, R0127, R0130 del 2026-11-14: "calles muy angostas, aceras muy angostas")
    "Calle Capitán Agustín Ravelo": 16.0,
    "Calle Batalla de Junín": 12.5,
    "Calle Aniceto Arce": 14.5,
    "Calle José Álvarez de Arenales": 12.5,
    "Calle Fray José Antonio de San Alberto": 11.5,
    "Calle Pantaleón Dalence": 12.0,
    "Calle Argentina": 11.5,
    "Calle Nicolás Ortiz": 12.0,
    "Calle Estudiantes": 12.0,
    "Calle Real Audiencia": 12.0,
    "Calle Simón Bolívar": 12.0,
    "Calle Daniel Calvo": 11.5,
    "Calle España": 11.5,
    "Calle Grau": 12.0,
    "Calle Loa": 11.0,
    # Colón entre San Felipe Neri y la Plazuela Cochabamba (R0100: "la calle que separa la iglesia de la plazuela
    # también es más ancha"); solo da a la ampliación AMP_S
    "Calle Colón": 15.0,
    # avenida ancha (corrección R0060: "es una calle muy ancha, en las cuatro esquinas")
    "Avenida Hernando Siles Zuaso": 17.0,
}
ANCHO_DEF = 11.5
# Ensanche 2026-11-24 (pedido del usuario: "las calles son muy angostas, hay que ampliarlas; opción dos, todas las calles,
# +1 o 2 m según veas"; los buses pisaban la vereda). Se suma al ancho de fachada a fachada y va ENTERO a la calzada
# (las veredas no cambian). +2 m donde la calzada tenía ≤ 7 m (no cabían un bus y un auto estacionado) y en Arce (calle
# principal de los micros); +1 m donde ya había 9 m o más. La Peatonal de Junín (TRAMOS) conserva su sección. La vuelta
# de la plaza, +2 m (usuario, 2026-11-24: "sí, hay que ampliar la vuelta de la plaza, dos metros"): el borde del lado de
# la plaza sigue sobre P01 y la línea de fachada se corre 2 m hacia afuera.
ENSANCHE = {
    "Calle Capitán Agustín Ravelo": 1.0,
    "Calle Colón": 1.0,
    "Avenida Hernando Siles Zuaso": 1.0,
    "Plaza 25 de Mayo": 2.0,
}
ENSANCHE_DEF = 2.0
# Tramos con ancho propio (punto de referencia sobre el eje → ancho, vereda). Junín frente al Mercado Central, entre
# Ravelo y la calle siguiente (corrección del usuario R0045–R0049, 2026-11-12): "en toda esta cuadra, de ambos
# lados, las aceras son anchas" — postes y árboles junto al bordillo y una acera ancha hasta las fachadas.
# Corrección 2026-11-13 (R0087 y fotos de Peatonal/): es la PEATONAL de Junín, recta, de ~11 m de fachada a fachada
# (huellas del lienzo a ±5 m del eje): calzada de adoquín de ~5 m para un solo vehículo, sin marcas, bolardos en los
# dos bordillos y veredas de 3 m llenas de puestos. El eje de OSM tenía quiebres falsos de ±15°: se endereza.
# (nombre, punto de referencia, ancho, vereda, opciones)
# Aclaración del usuario (2026-11-13): "la parte para los autos sí es angosta, pero las aceras son muy anchas, más de
# lo normal, sobre todo la acera derecha" (caminando desde Ravelo: la del Mercado, lado SE). Sección: vereda NO 3,5 m
# (fachada cerca del lienzo), calzada 5 m, vereda SE 6 m → 14,5 m. El eje se corre 2,25 m hacia el SE.
TRAMOS = [("Calle Batalla de Junín", (-180.0, 108.0), 14.5, 3.5,
           {"recto": True, "peatonal": True, "desplazar": -2.25, "vereda_izq": 3.5, "vereda_der": 6.0})]
# Arenales y Junín al oeste (R0119, R0122): vereda de 2,8 m quitándole a la calzada, sin recortar fachadas
VEREDAS = {"Calle Capitán Agustín Ravelo": 3.0, "Calle Aniceto Arce": 2.8, "Calle José Álvarez de Arenales": 2.8,
           "Calle Batalla de Junín": 2.8, "Calle Colón": 3.0, "Avenida Hernando Siles Zuaso": 2.6}
VEREDA_DEF = 2.2
# Veredas más anchas (2026-11-18, modo noche: postes junto al bordillo): +0,3 m en las de 2,2 y 2,8 m, sin bajar la
# calzada ORIGINAL (sin el ensanche) de 6,6 m ni pasar de 3 m. Hernando Siles queda en 2,8 m.
VEREDA_MAS, VEREDA_TOPE, CALZADA_MIN = 0.3, 3.0, 6.6
VEREDA_FIJA = {"Avenida Hernando Siles Zuaso": 2.8}


def vereda_de(nombre, ancho_original):
    if nombre in VEREDA_FIJA:
        return VEREDA_FIJA[nombre]
    v = VEREDAS.get(nombre, VEREDA_DEF)
    if v in (2.2, 2.8):
        v = min(v + VEREDA_MAS, VEREDA_TOPE, (ancho_original - CALZADA_MIN) / 2)
    return round(v, 2)
# Vereda que se prolonga por debajo de la línea de fachada (m): donde las fachadas reales quedan retiradas del borde
# del corredor y entre la vereda y la puerta se veía un hueco (R0112, Nicolás Ortiz, 2026-11-14).
VEREDA_EXTRA = {"Calle Nicolás Ortiz": 1.6}
# Calles con el eje de OSM tal cual (sin corrimiento hacia el medio de las fachadas del lienzo): alrededor de San
# Felipe Neri y la Plazuela Cochabamba el lienzo tiene pocas fachadas y la mediana corría Colón 2,4 m, dejando una
# franja entre el templo y la calle que el relleno llenaba de casas (control de calidad 2026-11-13).
EJE_OSM = {"Calle Colón", "Calle Juan José Pérez", "Calle Azurduy"}
# Calzadas alrededor de la Plaza 25 de Mayo (corrección del usuario R0001, 2026-11-12: "la zona de la plaza tiene
# calles más anchas, caben varios autos"): el corredor va desde el borde de la plaza (P01) hasta las fachadas, sin
# dejar franjas vacías. Su ancho es el espacio real entre la plaza y las huellas (entre ANCHO_PLAZA_MIN y _MAX); el
# eje se corre para que el borde del lado de la plaza coincida con P01. Las huellas se recortan como en las demás.
PLAZA = "Plaza 25 de Mayo"
ANCHO_PLAZA_MIN, ANCHO_PLAZA_MAX = 12.5, 16.0
VEREDA_PLAZA = 3.0   # R0109/R0122 (2026-11-14): "le falta anchura a la acera"; la calzada de la plaza sigue holgada
SIN_RECORTE = set()
TIPOS_FUERA = {"footway", "pedestrian", "steps", "path", "service", "cycleway"}


def cargar(rel):
    with open(os.path.join(RAIZ, rel)) as fh:
        return json.load(fh)


def main():
    rep = cargar("reparto/manzanas.json")
    z = rep["zona"]
    m = 25
    cajas_ = [(z["xmin"] - m, z["ymin"] - m, z["xmax"] + m, z["ymax"] + m)]
    for e_ in rep.get("espacios", []):                 # ampliaciones (AMP_*) fuera de la zona original
        if e_["id"] in ("AMP_S",) and e_.get("poligono"):
            xs_ = [p[0] for p in e_["poligono"]]
            ys_ = [p[1] for p in e_["poligono"]]
            cajas_.append((min(xs_) - m, min(ys_) - m, max(xs_) + m, max(ys_) + m))
    dentro = lambda x, y: any(c_[0] < x < c_[2] and c_[1] < y < c_[3] for c_ in cajas_)
    edif = cargar("reparto/edificios_lienzo.json")

    segs = []
    for e in edif:
        h = e["huella"]
        segs += [(tuple(h[i]), tuple(h[(i + 1) % len(h)])) for i in range(len(h))]
    grilla = defaultdict(list)
    for s in segs:
        (x1, y1), (x2, y2) = s
        for gx in range(int(min(x1, x2) // 10), int(max(x1, x2) // 10) + 1):
            for gy in range(int(min(y1, y2) // 10), int(max(y1, y2) // 10) + 1):
                grilla[(gx, gy)].append(s)

    def rayo(px, py, dx, dy, maxd=16.0):
        mejor, cand = maxd, set()
        t = 0.0
        while t <= maxd:
            x, y = px + dx * t, py + dy * t
            for gx in (int(x // 10) - 1, int(x // 10), int(x // 10) + 1):
                for gy in (int(y // 10) - 1, int(y // 10), int(y // 10) + 1):
                    cand.update(grilla.get((gx, gy), []))
            t += 5
        for (x1, y1), (x2, y2) in cand:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            tt = ((x1 - px) * ey - (y1 - py) * ex) / den
            u = ((x1 - px) * dy - (y1 - py) * dx) / den
            if 0 <= u <= 1 and 0 < tt < mejor:
                mejor = tt
        return mejor

    p01 = next(e["poligono"] for e in rep["espacios"] if e["id"] == "P01")
    segs_p01 = [(tuple(p01[i]), tuple(p01[(i + 1) % len(p01)])) for i in range(len(p01))]

    def rayo_plaza(px, py, dx, dy, maxd=14.0):
        mejor = maxd
        for (x1, y1), (x2, y2) in segs_p01:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-9:
                continue
            tt = ((x1 - px) * ey - (y1 - py) * ex) / den
            u = ((x1 - px) * dy - (y1 - py) * dx) / den
            if 0 <= u <= 1 and 0 < tt < mejor:
                mejor = tt
        return mejor

    salida = []
    for c in cargar("web/public/mapa/calles.json"):
        if not c["nombre"] or c["tipo"] in TIPOS_FUERA:
            continue
        pts = [tuple(p[:2]) for p in c["puntos"]]
        if not any(dentro(*p) for p in pts):
            continue
        # cada tramo recto de OSM se corre EN PARALELO hasta el punto medio entre las fachadas del lienzo
        # (mediana de muestras cada 2 m); así los bordes del corredor quedan rectos
        ensanche = ENSANCHE.get(c["nombre"], ENSANCHE_DEF)
        ancho_original = ANCHOS.get(c["nombre"], ANCHO_DEF)
        ancho = ancho_original + ensanche
        anchos_plaza = []
        lineas = []
        for a, b in zip(pts, pts[1:]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            if L < 0.5:
                continue
            ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            nx, ny = -uy, ux
            ds = []
            for k in range(max(1, int(L // 2)) + 1):
                t = min(L, k * 2.0)
                x, y = a[0] + ux * t, a[1] + uy * t
                izq, der = rayo(x, y, nx, ny), rayo(x, y, -nx, -ny)
                if izq < 14 and der < 14:
                    ds.append((izq - der) / 2)
            d = sorted(ds)[len(ds) // 2] if len(ds) >= max(2, len(ds) // 3) and ds else None
            if c["nombre"] == PLAZA:
                d = None
                pl, ed = [], []
                for k in range(max(1, int(L // 2)) + 1):
                    t = min(L, k * 2.0)
                    x, y = a[0] + ux * t, a[1] + uy * t
                    for sg in (1, -1):
                        dp = rayo_plaza(x, y, nx * sg, ny * sg)
                        if dp < 14:
                            pl.append((sg, dp))
                            ed.append(rayo(x, y, -nx * sg, -ny * sg, 30.0))
                if len(pl) >= 2:
                    sg = sorted(q[0] for q in pl)[len(pl) // 2]
                    dp = sorted(q[1] for q in pl if q[0] == sg)[len([q for q in pl if q[0] == sg]) // 2]
                    de = sorted(ed)[len(ed) // 2]
                    w = max(ANCHO_PLAZA_MIN + ensanche, min(ANCHO_PLAZA_MAX + ensanche, dp + de))
                    # el borde del lado de la plaza queda sobre P01; el eje, a w/2 de él hacia las fachadas
                    d = sg * (dp - w / 2)
                    anchos_plaza.append(w)
            lineas.append([a, b, nx, ny, d, L])
        if not lineas:
            continue
        # tramos sin dato: toman el desplazamiento del vecino más cercano que tenga
        for i, ln in enumerate(lineas):
            if ln[4] is None:
                ma = ((ln[0][0] + ln[1][0]) / 2, (ln[0][1] + ln[1][1]) / 2)
                if not (z["xmin"] - m < ma[0] < z["xmax"] + m and z["ymin"] - m < ma[1] < z["ymax"] + m):
                    # fuera de la zona no hay fachadas del lienzo para medir: se respeta el eje de OSM (antes copiaba
                    # el corrimiento del tramo vecino y Colón quedaba 3 m corrida, con casas de relleno junto al templo)
                    ln[4] = 0.0
                    continue
                vec = [lineas[j][4] for j in sorted(range(len(lineas)), key=lambda j: abs(j - i)) if lineas[j][4] is not None]
                ln[4] = vec[0] if vec else 0.0
            ln[4] = max(-3.0, min(3.0, ln[4])) if c["nombre"] != PLAZA else max(-6.0, min(6.0, ln[4]))
            if c["nombre"] in EJE_OSM:
                ln[4] = 0.0
        if anchos_plaza:
            ancho = round(sorted(anchos_plaza)[len(anchos_plaza) // 2], 1)
        des = [((a[0] + nx * d, a[1] + ny * d), (b[0] + nx * d, b[1] + ny * d)) for a, b, nx, ny, d, _ in lineas]
        eje = [des[0][0]]
        for (p1, p2), (q1, q2) in zip(des, des[1:]):
            # unión: intersección de las dos rectas (o el punto medio si son casi paralelas)
            r = (p2[0] - p1[0], p2[1] - p1[1])
            s_ = (q2[0] - q1[0], q2[1] - q1[1])
            den = r[0] * s_[1] - r[1] * s_[0]
            if abs(den) > 1e-6 * math.hypot(*r) * math.hypot(*s_):
                t = ((q1[0] - p1[0]) * s_[1] - (q1[1] - p1[1]) * s_[0]) / den
                x = (p1[0] + r[0] * t, p1[1] + r[1] * t)
                if math.hypot(x[0] - p2[0], x[1] - p2[1]) < 4:
                    eje.append(x)
                    continue
            eje.append(((p2[0] + q1[0]) / 2, (p2[1] + q1[1]) / 2))
        eje.append(des[-1][1])
        eje = [[round(x, 2), round(y, 2)] for x, y in eje]
        opciones = {}
        for nom_t, ref, ancho_t, vereda_t, opc in TRAMOS:
            if c["nombre"] == nom_t and min(math.hypot(x - ref[0], y - ref[1]) for x, y in eje) < 10:
                ancho = ancho_t
                vereda_tramo = vereda_t
                opciones = opc
                break
        else:
            vereda_tramo = None
        if opciones.get("recto") and len(eje) > 2:
            # recta de ajuste (componente principal) entre las proyecciones de los extremos
            mx = sum(p[0] for p in eje) / len(eje)
            my = sum(p[1] for p in eje) / len(eje)
            sxx = sum((p[0] - mx) ** 2 for p in eje)
            syy = sum((p[1] - my) ** 2 for p in eje)
            sxy = sum((p[0] - mx) * (p[1] - my) for p in eje)
            ang = 0.5 * math.atan2(2 * sxy, sxx - syy)
            ux, uy = math.cos(ang), math.sin(ang)
            ts = [(p[0] - mx) * ux + (p[1] - my) * uy for p in eje]
            eje = [[round(mx + ux * t, 2), round(my + uy * t, 2)] for t in (min(ts), max(ts))]
        if opciones.get("desplazar"):
            # corrimiento en paralelo hacia la izquierda (+) o la derecha (−) del sentido del eje
            (x0, y0), (x1, y1) = eje[0], eje[-1]
            L_ = math.hypot(x1 - x0, y1 - y0)
            nx_, ny_ = -(y1 - y0) / L_, (x1 - x0) / L_
            dd = opciones["desplazar"]
            eje = [[round(x + nx_ * dd, 2), round(y + ny_ * dd, 2)] for x, y in eje]
        tramo = {
            "nombre": c["nombre"], "tipo": c["tipo"], "ancho": ancho,
            "vereda": vereda_tramo or (VEREDA_PLAZA if c["nombre"] == PLAZA else vereda_de(c["nombre"], ancho_original)),
            "recortar": c["nombre"] not in SIN_RECORTE, "eje": eje,
        }
        if opciones.get("peatonal"):
            tramo["peatonal"] = True
        if c["nombre"] in VEREDA_EXTRA:
            tramo["vereda_extra"] = VEREDA_EXTRA[c["nombre"]]
        for k in ("vereda_izq", "vereda_der"):
            if k in opciones:
                tramo[k] = opciones[k]
        salida.append(tramo)

    doc = {
        "descripcion": "Calles con ancho real (fachada a fachada). Lo generó scripts/calles_reales.py. "
                       "El kit recorta las huellas para que ninguna fachada entre en el corredor; la BASE "
                       "construye calzada, veredas y bordillos con estos datos.",
        "calles": salida,
    }
    with open(os.path.join(RAIZ, "reparto", "calles_reales.json"), "w") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
    print(f"{len(salida)} tramos de calle → reparto/calles_reales.json")


if __name__ == "__main__":
    main()
