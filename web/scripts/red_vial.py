#!/usr/bin/env python3
"""Red de carriles para el tráfico de la ciudad → web/public/trafico/red.json (coordenadas web: x, y arriba, z = −norte).

De dónde sale cada cosa (sin datos nuevos a mano):
- Topología, cruces y SENTIDO de circulación: Sucre.osm.gz (casi todo el centro es de sentido único).
- Posición de cada calle dentro de la zona modelada: el eje REAL de reparto/calles_reales.json (el mismo con el que la
  BASE construye calzada y veredas). Los nodos de OSM se proyectan sobre ese eje; los cruces, sobre la intersección de
  los dos ejes. Dentro de la zona solo circulan las calles que tienen calzada modelada (nada atraviesa manzanas).
- Ancho de calzada: calles_reales (ancho − 2 veredas) o, dentro de una sección (secciones/*.json), su campo 'calzadas'.
- Altura: reparto/terreno.json + 7 cm (como base_suelo.SOBRE_TERRENO).
- Fuera de la zona, la red sigue unos 90 m por las calles de OSM (sobre el terreno del lienzo): por ahí entran y salen
  los vehículos, lejos de la vista.

Carriles: uno por sentido. En sentido único el vehículo va por el CENTRO de la calzada (las del casco viejo son
angostas: corrido a un lado roza el bordillo y en las esquinas no le da el giro); en doble sentido, en el centro de su
mitad. En cada cruce se unen el final de un carril y el comienzo de otro con un arco (Bézier cúbica de arco de
circunferencia) que empieza RADIO_GIRO m antes del centro del cruce: un radio que el micro puede dar sin subirse a la
vereda. Se revisa con web/scripts/red_vial_revisar.py.

Uso: python3 web/scripts/red_vial.py
"""
import glob
import gzip
import json
import math
import os
import xml.etree.ElementTree as ET
from collections import defaultdict

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SAL = os.path.join(RAIZ, "web", "public", "trafico", "red.json")

# --- mismas constantes que web/src/mapa/geo.ts y blender/scripts/geo.py
LAT0, LON0, R, DX, DY = -19.046, -65.2578, 6378137, 4.69, 3.09
KX = math.pi / 180 * R * math.cos(math.radians(LAT0))
KY = math.pi / 180 * R

VIAS = {"primary", "secondary", "tertiary", "residential", "unclassified", "living_street",
        "primary_link", "secondary_link", "tertiary_link"}
SOBRE_TERRENO = 0.07
MARGEN_FUERA = 90.0       # m de red que se conservan fuera de la zona modelada
SNAP = 9.0                # m: distancia máxima de un nodo de OSM al eje real de su calle
CALZADA_FUERA = 8.0       # m: ancho supuesto de las calles fuera de la zona
PASO = 1.0                # m entre puntos de los carriles
PASADAS_SUAVIZADO = 150   # dobladas dentro de una misma calle: ver redondear()
RADIO_GIRO = 7.0          # m: las curvas de cruce empiezan al menos esto antes del centro del cruce (radio del arco)
# Límites (m/s). Subidos el 2026-11-26 (pedido del usuario: "deben ir más rápido, el usuario no debería alcanzarlos ni
# corriendo"; el caminante corre a 5,5 m/s): 40–50 km/h por las calles, 35 km/h alrededor de la plaza.
VEL_MAX = {"primary": 13.9, "secondary": 13.9, "tertiary": 12.5, "residential": 11.1, "unclassified": 11.1, "living_street": 6.0}
VEL_PLAZA = 9.7           # alrededor de la plaza algo más despacio (peatones, cruces seguidos)


def a_metros(lat, lon):
    return ((lon - LON0) * KX + DX, (lat - LAT0) * KY + DY)


def cargar(ruta):
    return json.load(open(os.path.join(RAIZ, ruta)))


TERRENO = cargar("reparto/terreno.json")


def altura(x, y):
    t = TERRENO
    ox, oy = t["origen"]
    p, n, z = t["paso"], t["n"], t["z"]
    fx, fy = (x - ox) / p, (y - oy) / p
    i, j = max(0, min(n - 2, int(fx))), max(0, min(n - 2, int(fy)))
    u, v = fx - i, fy - j
    return z[j][i] * (1 - u) * (1 - v) + z[j][i + 1] * u * (1 - v) + z[j + 1][i] * (1 - u) * v + z[j + 1][i + 1] * u * v


def dentro(x, y, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def proyectar(p, eje):
    """(distancia, punto) del punto p sobre la polilínea eje."""
    mejor = (1e18, None)
    for a, b in zip(eje, eje[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l2 = dx * dx + dy * dy or 1e-9
        t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l2))
        q = (a[0] + t * dx, a[1] + t * dy)
        d = math.hypot(p[0] - q[0], p[1] - q[1])
        if d < mejor[0]:
            mejor = (d, q)
    return mejor


# ------------------------------------------------------------------------------------------------ zona y calles reales
reparto = cargar("reparto/manzanas.json")
z = reparto["zona"]
CAJAS = [(z["xmin"], z["ymin"], z["xmax"], z["ymax"]), (-235.0, 95.0, -55.0, 235.0)]  # + ampliación de Junín (BASE)
POLIGONOS = [e["poligono"] for e in reparto.get("espacios", []) if e.get("poligono")]


def en_zona(x, y, margen=10.0):
    if any(x0 - margen <= x <= x1 + margen and y0 - margen <= y <= y1 + margen for x0, y0, x1, y1 in CAJAS):
        return True
    return any(dentro(x, y, p) for p in POLIGONOS)


SECCIONES = [json.load(open(r)) for r in glob.glob(os.path.join(RAIZ, "secciones", "*.json"))]
REALES = [c for c in cargar("reparto/calles_reales.json")["calles"] if not c.get("peatonal")]
POR_NOMBRE = defaultdict(list)
for c in REALES:
    POR_NOMBRE[c["nombre"]].append(c)


def calzada_en(nombre, x, y, real):
    for s in SECCIONES:
        if s.get("limite") and dentro(x, y, s["limite"]) and nombre in s.get("calzadas", {}):
            return s["calzadas"][nombre]
    if real is None:
        return CALZADA_FUERA
    izq, der = real.get("vereda_izq", real["vereda"]), real.get("vereda_der", real["vereda"])
    return real["ancho"] - izq - der


def eje_cercano(nombre, p):
    mejor = (1e18, None, None)
    for c in POR_NOMBRE.get(nombre, []):
        d, q = proyectar(p, c["eje"])
        if d < mejor[0]:
            mejor = (d, q, c)
    return mejor


# ------------------------------------------------------------------------------------------------------------- OSM
def leer_osm():
    nodos, vias = {}, []
    for _, el in ET.iterparse(gzip.open(os.path.join(RAIZ, "Sucre.osm.gz"))):
        if el.tag == "node":
            nodos[el.get("id")] = a_metros(float(el.get("lat")), float(el.get("lon")))
        elif el.tag == "way":
            tags = {t.get("k"): t.get("v") for t in el.findall("tag")}
            if tags.get("highway") in VIAS and tags.get("access") not in ("no", "private"):
                vias.append({"nodos": [n.get("ref") for n in el.findall("nd")], "nombre": tags.get("name", ""),
                             "tipo": tags["highway"], "oneway": tags.get("oneway", "no"),
                             "rotonda": tags.get("junction") == "roundabout"})
            el.clear()
        elif el.tag == "relation":
            el.clear()
    return nodos, vias


def construir():
    nodos_osm, vias = leer_osm()
    x0 = min(c[0] for c in CAJAS) - MARGEN_FUERA - 200
    y0 = min(c[1] for c in CAJAS) - MARGEN_FUERA - 200
    x1 = max(c[2] for c in CAJAS) + MARGEN_FUERA + 200
    y1 = max(c[3] for c in CAJAS) + MARGEN_FUERA + 200
    vias = [v for v in vias if any(x0 <= nodos_osm[n][0] <= x1 and y0 <= nodos_osm[n][1] <= y1 for n in v["nodos"] if n in nodos_osm)]

    # nombres de las calles que pasan por cada nodo (un cruce se proyecta sobre la intersección de sus ejes)
    calles_nodo = defaultdict(set)
    uso = defaultdict(int)
    for v in vias:
        for n in v["nodos"]:
            calles_nodo[n].add(v["nombre"])
            uso[n] += 1
        uso[v["nodos"][0]] += 1
        uso[v["nodos"][-1]] += 1

    # posición de cada nodo: (x, y, estado) estado = "real" (sobre el eje modelado), "fuera" (OSM tal cual), None (no sirve)
    pos = {}
    real_de = {}
    for n, nombres in calles_nodo.items():
        if n not in nodos_osm:
            continue
        p = nodos_osm[n]
        ejes = [(nom,) + eje_cercano(nom, p) for nom in nombres if nom in POR_NOMBRE]
        ejes = [e for e in ejes if e[1] < SNAP]
        if ejes:
            q = ejes[0][2]
            if len(ejes) > 1:  # proyecciones alternadas: converge a la intersección de los ejes
                for _ in range(12):
                    for nom, *_ in ejes:
                        q = eje_cercano(nom, q)[1]
            pos[n] = (q[0], q[1], "real")
            real_de[n] = {e[0]: e[3] for e in ejes}
        elif not en_zona(*p):
            pos[n] = (p[0], p[1], "fuera")
        else:
            pos[n] = None

    # distancia de cada nodo "fuera" a la zona (por la red): se conservan los primeros MARGEN_FUERA metros
    vecinos = defaultdict(list)
    for v in vias:
        for a, b in zip(v["nodos"], v["nodos"][1:]):
            if pos.get(a) and pos.get(b):
                d = math.hypot(pos[a][0] - pos[b][0], pos[a][1] - pos[b][1])
                vecinos[a].append((b, d))
                vecinos[b].append((a, d))
    dist = {n: 0.0 for n, p in pos.items() if p and p[2] == "real"}
    frente = list(dist)
    while frente:
        nuevo = []
        for a in frente:
            for b, d in vecinos[a]:
                if pos[b][2] != "fuera":
                    continue
                nd = dist[a] + d
                if nd < dist.get(b, 1e18) and nd <= MARGEN_FUERA + d:
                    dist[b] = nd
                    nuevo.append(b)
        frente = nuevo

    def sirve(n):
        p = pos.get(n)
        return bool(p) and n in dist

    # tramos: trozos de vía entre nodos de cruce (o extremos), con sus sentidos permitidos
    tramos = []
    for v in vias:
        ns = v["nodos"]
        ow = v["oneway"]
        sentidos = (1,) if ow in ("yes", "true", "1") or v["rotonda"] else (-1,) if ow == "-1" else (1, -1)
        actual = []
        for k, n in enumerate(ns):
            if not sirve(n):
                if len(actual) >= 2:
                    tramos.append((actual, v, sentidos))
                actual = []
                continue
            actual.append(n)
            corte = uso[n] > 1 and 0 < k < len(ns) - 1
            if corte and len(actual) >= 2:
                tramos.append((actual, v, sentidos))
                actual = [n]
        if len(actual) >= 2:
            tramos.append((actual, v, sentidos))

    # -------------------------------------------------------------------------------------------- carriles
    carriles = []
    for ns, v, sentidos in tramos:
        pts = [(pos[n][0], pos[n][1]) for n in ns]
        largo = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:]))
        if largo < 0.5:
            continue
        medio = pts[len(pts) // 2]
        real = None
        for n in ns:
            if n in real_de and v["nombre"] in real_de[n]:
                real = real_de[n][v["nombre"]]
                break
        calz = calzada_en(v["nombre"], medio[0], medio[1], real)
        doble = len(sentidos) == 2
        # sentido único: por el centro de la calzada; doble sentido: centro de su mitad
        desplazo = calz / 4 if doble else 0.0
        # el trazado sigue el eje REAL entre nodos (unirlos en línea recta se aparta de la calzada en las cuadras curvas)
        if real is not None:
            pts = por_eje(pts, [pos[n][2] == "real" for n in ns], POR_NOMBRE[v["nombre"]])
        en_plaza = v["nombre"] == "Plaza 25 de Mayo"
        vmax = VEL_PLAZA if en_plaza else VEL_MAX.get(v["tipo"].replace("_link", ""), 11.1)
        for s in sentidos:
            orden = ns if s == 1 else ns[::-1]
            carriles.append({"nodos": orden, "pts": pts if s == 1 else pts[::-1], "calle": v["nombre"],
                             "desplazo": desplazo, "calzada": calz, "vmax": vmax, "fuera": real is None})

    # ancho de calzada de cada cruce (para empezar las curvas antes del bordillo de la calle transversal)
    calz_nodo = defaultdict(float)
    for c in carriles:
        for n in (c["nodos"][0], c["nodos"][-1]):
            calz_nodo[(n, c["calle"])] = max(calz_nodo[(n, c["calle"])], c["calzada"])

    def recorte(c, n):
        otras = [w for (m, calle), w in calz_nodo.items() if m == n and calle != c["calle"]]
        if not otras:   # curva de una misma calle o unión de dos vías: curva corta
            return 2.0
        return max(RADIO_GIRO, max(otras) / 2 + 0.8)

    sal_carriles = []
    for c in carriles:
        holgura = c["calzada"] / 2 - abs(c["desplazo"]) - 1.6   # cuánto puede correrse el carril hacia adentro
        pts = c["pts"] if c["fuera"] else redondear(c["pts"], PASADAS_SUAVIZADO, max(0.3, holgura))
        linea = desplazar(suavizar(pts), c["desplazo"])
        largo = longitud(linea)
        r0 = recorte(c, c["nodos"][0]) if uso[c["nodos"][0]] > 1 else 0.0
        r1 = recorte(c, c["nodos"][-1]) if uso[c["nodos"][-1]] > 1 else 0.0
        if r0 + r1 > largo - 1.0:
            k = max(0.0, (largo - 1.0) / max(r0 + r1, 1e-6))
            r0, r1 = r0 * k, r1 * k
        linea = recortar(linea, r0, largo - r1)
        if longitud(linea) < 0.8:
            continue
        sal_carriles.append({**c, "linea": linea})

    # ---------------------------------------------------------------------------------------- conectores
    llegan, salen = defaultdict(list), defaultdict(list)
    for i, c in enumerate(sal_carriles):
        llegan[c["nodos"][-1]].append(i)
        salen[c["nodos"][0]].append(i)
    conectores = []
    for n, ins in llegan.items():
        for i in ins:
            a = sal_carriles[i]
            opciones = [j for j in salen.get(n, []) if not (sal_carriles[j]["nodos"][::-1] == a["nodos"])]
            if not opciones:   # sin salida que no sea dar la vuelta: se admite el giro en U solo si hay espacio
                opciones = [j for j in salen.get(n, []) if a["calzada"] >= 9]
            for j in opciones:
                b = sal_carriles[j]
                p0, p1 = a["linea"][-1], a["linea"][-2]
                q0, q1 = b["linea"][0], b["linea"][1]
                d0 = unitario(p0[0] - p1[0], p0[1] - p1[1])
                d1 = unitario(q1[0] - q0[0], q1[1] - q0[1])
                giro = math.atan2(d0[0] * d1[1] - d0[1] * d1[0], d0[0] * d1[0] + d0[1] * d1[1])
                if abs(giro) > math.radians(120):
                    continue   # giros casi en U (las V de las esquinas de la plaza en OSM): el micro no los da
                cuerda = math.hypot(q0[0] - p0[0], q0[1] - p0[1])
                if abs(giro) > 0.15:   # arco de circunferencia por la cuerda: curvatura pareja, sin cerrarse al medio
                    k = 4 / 3 * math.tan(abs(giro) / 4) * cuerda / (2 * math.sin(abs(giro) / 2))
                else:
                    k = cuerda * 0.35
                curva = bezier(p0, (p0[0] + d0[0] * k, p0[1] + d0[1] * k), (q0[0] - d1[0] * k, q0[1] - d1[1] * k), q0)
                conectores.append({"de": i, "a": j, "nodo": n, "linea": curva, "giro": giro})

    # ---------------------------------------------- se queda la parte conectada (sin carriles sueltos ni callejones)
    sig = defaultdict(list)
    for c in conectores:
        sig[c["de"]].append(c["a"])
    componente = mayor_fuertemente_conexa(len(sal_carriles), sig)
    alcanza = cerradura(componente, sig)                                 # salidas
    inv = defaultdict(list)
    for a, bs in sig.items():
        for b in bs:
            inv[b].append(a)
    llega_a = cerradura(componente, inv)                                 # entradas
    vivos = sorted(alcanza | llega_a)
    nuevo = {v: k for k, v in enumerate(vivos)}

    def a_web(linea):
        out = []
        for x, y in linea:
            out += [round(x, 2), round(altura(x, y) + SOBRE_TERRENO, 3), round(-y, 2)]
        return out

    red = {
        "descripcion": "Red de carriles del tráfico. La genera web/scripts/red_vial.py (OSM + reparto/calles_reales.json + terreno).",
        "carriles": [{"calle": sal_carriles[i]["calle"], "vmax": sal_carriles[i]["vmax"],
                      "fuera": sal_carriles[i]["fuera"], "puntos": a_web(sal_carriles[i]["linea"])} for i in vivos],
        "conectores": [{"de": nuevo[c["de"]], "a": nuevo[c["a"]], "nodo": c["nodo"], "giro": round(c["giro"], 3),
                        "puntos": a_web(c["linea"])} for c in conectores if c["de"] in nuevo and c["a"] in nuevo],
    }
    os.makedirs(os.path.dirname(SAL), exist_ok=True)
    json.dump(red, open(SAL, "w"), separators=(",", ":"))
    total = sum(longitud(sal_carriles[i]["linea"]) for i in vivos)
    dentro_m = sum(longitud(sal_carriles[i]["linea"]) for i in vivos if not sal_carriles[i]["fuera"])
    print(f"{len(vivos)} carriles ({total:.0f} m, {dentro_m:.0f} m en la zona), {len(red['conectores'])} conectores "
          f"→ {os.path.relpath(SAL, RAIZ)} ({os.path.getsize(SAL) // 1024} KB)")


# --------------------------------------------------------------------------------------------- geometría de polilíneas
def parametro(p, eje):
    """Distancia a lo largo del eje de la proyección de p."""
    mejor, acum, t_mejor = 1e18, 0.0, 0.0
    for a, b in zip(eje, eje[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        l = math.hypot(dx, dy) or 1e-9
        t = max(0.0, min(l, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / l))
        d = math.hypot(a[0] + dx * t / l - p[0], a[1] + dy * t / l - p[1])
        if d < mejor:
            mejor, t_mejor = d, acum + t
        acum += l
    return t_mejor, mejor


def tramo_eje(eje, t0, t1):
    """Trozo del eje entre las distancias t0 y t1 (en ese sentido)."""
    inv = t0 > t1
    a0, a1 = (t1, t0) if inv else (t0, t1)
    l = recortar([tuple(q) for q in eje], a0, a1)
    return l[::-1] if inv else l


def por_eje(pts, reales, calles):
    """La polilínea pts, pero donde dos nodos seguidos están cerca de un mismo eje real, sobre ese eje (proyectados).
    En los cruces cuyos ejes no llegan a cortarse el nodo queda entre los dos: así el carril no cruza en diagonal."""
    out = []
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        trozo = [a, b]
        if reales[k] and reales[k + 1]:
            for c in calles:
                (t0, d0), (t1, d1) = parametro(a, c["eje"]), parametro(b, c["eje"])
                if d0 < SNAP and d1 < SNAP and abs(t1 - t0) > 0.3:
                    trozo = tramo_eje(c["eje"], t0, t1)
                    break
        if out and math.hypot(out[-1][0] - trozo[0][0], out[-1][1] - trozo[0][1]) < 0.05:
            trozo = trozo[1:]
        out += trozo
    return out


def unitario(x, y):
    l = math.hypot(x, y) or 1e-9
    return (x / l, y / l)


def longitud(l):
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(l, l[1:]))


def remuestrear(l, paso):
    out = [l[0]]
    resto = 0.0
    for a, b in zip(l, l[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        t = paso - resto
        while t <= seg:
            out.append((a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg))
            t += paso
        resto = seg - (t - paso)
    if math.hypot(out[-1][0] - l[-1][0], out[-1][1] - l[-1][1]) > 0.05:
        out.append(l[-1])
    return out


def redondear(l, pasadas, desvio_max):
    """Abre las dobladas de una misma calle (las esquinas de la plaza): puntos cada metro y suavizado laplaciano
    repetido, con los extremos fijos y sin apartarse más de desvio_max de la polilínea original. Las esquinas quedan
    con un radio que el micro puede seguir sin salirse de la calzada."""
    q = remuestrear(l, 1.0)
    if len(q) < 6:
        return l
    orig = list(q)
    for _ in range(pasadas):
        n = q[:2]
        for i in range(2, len(q) - 2):
            x = 0.5 * q[i][0] + 0.25 * (q[i - 1][0] + q[i + 1][0])
            y = 0.5 * q[i][1] + 0.25 * (q[i - 1][1] + q[i + 1][1])
            dx, dy = x - orig[i][0], y - orig[i][1]
            d = math.hypot(dx, dy)
            if d > desvio_max:
                x, y = orig[i][0] + dx * desvio_max / d, orig[i][1] + dy * desvio_max / d
            n.append((x, y))
        q = n + q[-2:]
    return q


def suavizar(l):
    """Chaikin (2 pasadas) conservando los extremos, luego puntos cada PASO metros: tangentes continuas."""
    for _ in range(2):
        if len(l) < 3:
            break
        n = [l[0]]
        for a, b in zip(l, l[1:]):
            n.append((0.75 * a[0] + 0.25 * b[0], 0.75 * a[1] + 0.25 * b[1]))
            n.append((0.25 * a[0] + 0.75 * b[0], 0.25 * a[1] + 0.75 * b[1]))
        n.append(l[-1])
        l = n
    return remuestrear(l, PASO)


def desplazar(l, d):
    """Corre la polilínea d metros a la DERECHA del sentido de marcha."""
    if abs(d) < 1e-6:
        return l
    out = []
    for i, p in enumerate(l):
        a, b = l[max(0, i - 1)], l[min(len(l) - 1, i + 1)]
        tx, ty = unitario(b[0] - a[0], b[1] - a[1])
        out.append((p[0] + ty * d, p[1] - tx * d))   # derecha de (tx, ty) en x este / y norte
    return out


def recortar(l, s0, s1):
    out = []
    s = 0.0
    for a, b in zip(l, l[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        for t in (s0, s1):
            if s < t < s + seg and seg > 0:
                q = (a[0] + (b[0] - a[0]) * (t - s) / seg, a[1] + (b[1] - a[1]) * (t - s) / seg)
                out.append((t, q))
        if s0 <= s <= s1:
            out.append((s, a))
        s += seg
    if s0 <= s <= s1:
        out.append((s, l[-1]))
    out.sort(key=lambda e: e[0])
    return [q for _, q in out]


def bezier(p0, p1, p2, p3):
    largo = math.hypot(p1[0] - p0[0], p1[1] - p0[1]) + math.hypot(p2[0] - p1[0], p2[1] - p1[1]) + math.hypot(p3[0] - p2[0], p3[1] - p2[1])
    n = max(2, int(largo / 0.5))
    out = []
    for k in range(n + 1):
        t = k / n
        u = 1 - t
        out.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return out


def mayor_fuertemente_conexa(n, sig):
    """Tarjan iterativo: el conjunto más grande de carriles desde los que se puede ir a todos los demás."""
    indice, bajo, pila, en_pila, comps = {}, {}, [], set(), []
    contador = [0]
    for raiz in range(n):
        if raiz in indice:
            continue
        trabajo = [(raiz, 0)]
        while trabajo:
            v, k = trabajo.pop()
            if k == 0:
                indice[v] = bajo[v] = contador[0]
                contador[0] += 1
                pila.append(v)
                en_pila.add(v)
            hijos = sig.get(v, [])
            seguir = False
            for i in range(k, len(hijos)):
                w = hijos[i]
                if w not in indice:
                    trabajo.append((v, i + 1))
                    trabajo.append((w, 0))
                    seguir = True
                    break
                if w in en_pila:
                    bajo[v] = min(bajo[v], indice[w])
            if seguir:
                continue
            if bajo[v] == indice[v]:
                comp = set()
                while True:
                    w = pila.pop()
                    en_pila.discard(w)
                    comp.add(w)
                    if w == v:
                        break
                comps.append(comp)
            if trabajo:
                padre = trabajo[-1][0]
                bajo[padre] = min(bajo[padre], bajo[v])
    return max(comps, key=len)


def cerradura(inicio, sig):
    vistos = set(inicio)
    frente = list(inicio)
    while frente:
        v = frente.pop()
        for w in sig.get(v, []):
            if w not in vistos:
                vistos.add(w)
                frente.append(w)
    return vistos


if __name__ == "__main__":
    construir()
