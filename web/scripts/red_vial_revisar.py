#!/usr/bin/env python3
"""Revisa la red del tráfico (web/public/trafico/red.json): ¿cabe el micro en la calzada al seguir cada carril y cada
curva de cruce?

Simula al conductor de ciudad3d/scripts/trafico/vehiculo.gd (persecución pura desde el eje trasero, con el mismo
alcance de mirada, giro máximo y rapidez de volante, a la velocidad de la curva) con un modelo de bicicleta, y en cada
paso mira los bordes de la caja del micro: si alguno queda fuera de la calzada modelada (eje real ± media calzada de
reparto/calles_reales.json o de la sección) lo cuenta como roce. Solo cruces entre calles con calzada modelada.

Uso: python3 web/scripts/red_vial_revisar.py [--todos]
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import red_vial as rv  # noqa: E402

VEH = json.load(open(os.path.join(rv.RAIZ, "ciudad3d", "datos", "vehiculos.json")))["tipos"]
DIRECCION_MINIMA = 0.62
ACEL_LATERAL = 1.5
DT = 0.05
TOLERANCIA = 0.15   # m fuera de la calzada que no cuentan (bordillo redondeado, muestreo)


def calles():
    out = []
    for c in rv.REALES:
        if c.get("peatonal"):
            continue
        vi, vd = c.get("vereda_izq", c["vereda"]), c.get("vereda_der", c["vereda"])
        out.append((c["nombre"], c["eje"], c["ancho"] - vi - vd, (vd - vi) / 2))
    return out


CALLES = calles()


def fuera_de_calzada(x, y):
    """Cuánto queda el punto fuera de la calzada más cercana (≤ 0: dentro)."""
    mejor = 1e9
    for nombre, eje, calz, off in CALLES:
        for s in rv.SECCIONES:
            if s.get("limite") and rv.dentro(x, y, s["limite"]) and nombre in s.get("calzadas", {}):
                calz = s["calzadas"][nombre]
        for a, b in zip(eje, eje[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            l2 = dx * dx + dy * dy or 1e-9
            t = ((x - a[0]) * dx + (y - a[1]) * dy) / l2
            if t < -0.02 or t > 1.02:
                continue
            l = math.sqrt(l2)
            lado = ((x - a[0]) * dy - (y - a[1]) * dx) / l       # + derecha
            mejor = min(mejor, abs(lado + off) - calz / 2)
        for p in eje:   # cruces donde un eje termina: tapa redonda
            mejor = min(mejor, math.hypot(x - p[0], y - p[1]) - calz / 2)
    return mejor


def recorrido(red, ids):
    pts = []
    for k, i in enumerate(ids):
        p = red[i]
        q = [(p[3 * j], -p[3 * j + 2]) for j in range(len(p) // 3)]
        pts += q[1:] if pts else q
    return pts


def simular(linea, kit):
    m = kit["movimiento"]
    L = m["eje_delantero"] - m["eje_trasero"]
    frente = kit["caja"]["max"][0] - m["eje_trasero"]
    cola = kit["caja"]["min"][0] - m["eje_trasero"]
    medio = kit["caja"]["max"][2] - 0.12
    maxima = max(m["direccion_maxima"], DIRECCION_MINIMA)
    rapidez = m["rapidez_direccion"] * 1.8
    s_acum = [0.0]
    for a, b in zip(linea, linea[1:]):
        s_acum.append(s_acum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))

    def punto(d):
        import bisect
        i = max(0, min(len(linea) - 2, bisect.bisect_right(s_acum, d) - 1))
        l = s_acum[i + 1] - s_acum[i] or 1e-9
        u = max(0.0, min(1.0, (d - s_acum[i]) / l))
        return (linea[i][0] + (linea[i + 1][0] - linea[i][0]) * u, linea[i][1] + (linea[i + 1][1] - linea[i][1]) * u)

    def curv(d):
        a, b, c = punto(d - 2), punto(d), punto(d + 2)
        t0 = math.atan2(b[1] - a[1], b[0] - a[0])
        t1 = math.atan2(c[1] - b[1], c[0] - b[0])
        g = (t1 - t0 + math.pi) % (2 * math.pi) - math.pi
        return abs(g) / 4

    x, y = linea[0]
    th = math.atan2(linea[1][1] - y, linea[1][0] - x)
    dirc = 0.0
    s = 0.0
    peor = (-1e9, None)
    total = s_acum[-1]
    while s < total - 8:
        vlim = min(m["velocidad_maxima"], min(math.sqrt(ACEL_LATERAL / max(curv(s + d), 1e-4)) for d in range(0, 14, 2)))
        v = vlim
        ld = max(4.5, min(16.0, 3.8 + 0.8 * v))
        o = punto(s + ld)
        lx, ly = o[0] - x, o[1] - y
        fwd = lx * math.cos(th) + ly * math.sin(th)
        izq = -lx * math.sin(th) + ly * math.cos(th)
        alfa = math.atan2(izq, fwd)
        deseada = max(-maxima, min(maxima, math.atan(2 * L * math.sin(alfa) / ld)))
        dirc += max(-rapidez * DT, min(rapidez * DT, deseada - dirc))
        x += v * math.cos(th) * DT
        y += v * math.sin(th) * DT
        th += v * math.tan(dirc) / L * DT
        # avance sobre el trazado: proyección cerca de s
        mejor = (1e9, s)
        for k in range(-5, 30):
            d = s + k * 0.2
            p = punto(d)
            e = math.hypot(p[0] - x, p[1] - y)
            if e < mejor[0]:
                mejor = (e, d)
        s = mejor[1]
        c, sn = math.cos(th), math.sin(th)
        for f in (cola, 0.0, frente * 0.5, frente):
            for w in (medio, -medio):
                px, py = x + c * f - sn * w, y + sn * f + c * w
                if not rv.en_zona(px, py, 0.0):
                    continue
                fu = fuera_de_calzada(px, py)
                if fu > peor[0]:
                    peor = (fu, (round(px, 1), round(py, 1)))
    return peor


def main():
    datos = json.load(open(rv.SAL))
    car = [c["puntos"] for c in datos["carriles"]]
    fuera = [c["fuera"] for c in datos["carriles"]]
    nc = len(car)
    con = datos["conectores"]
    todo = car + [k["puntos"] for k in con]
    kit = next(iter(VEH.values()))
    malos = []
    for i, k in enumerate(con):
        de, a = k["de"], k["a"]
        if fuera[de] or fuera[a]:
            continue   # entra o sale por una calle sin calzada modelada (OSM sobre el terreno del lienzo)
        lin_de = recorrido(todo, [de])
        lin = recorrido(todo, [de, nc + i, a])
        # desde 25 m antes del cruce hasta 25 m después
        acum, ini = 0.0, 0
        for j in range(len(lin_de) - 1, 0, -1):
            acum += math.hypot(lin_de[j][0] - lin_de[j - 1][0], lin_de[j][1] - lin_de[j - 1][1])
            if acum > 25:
                ini = j
                break
        sub = lin[ini:]
        acum, fin = 0.0, len(sub)
        for j in range(1, len(sub)):
            acum += math.hypot(sub[j][0] - sub[j - 1][0], sub[j][1] - sub[j - 1][1])
            if acum > 75:   # 25 m antes, la curva y unos 35 m después
                fin = j
                break
        fu, donde = simular(sub[:fin], kit)
        calle_de, calle_a = datos["carriles"][de]["calle"], datos["carriles"][a]["calle"]
        if fu > TOLERANCIA or "--todos" in sys.argv:
            malos.append((fu, calle_de, calle_a, k["giro"], donde))
    malos.sort(reverse=True)
    for fu, cd, ca, g, donde in malos:
        print(f"{fu:5.2f} m fuera  {cd} → {ca}  giro {math.degrees(g):5.0f}°  en {donde}")
    roces = [m for m in malos if m[0] > TOLERANCIA]
    print(f"{len(roces)} recorridos con roce (> {TOLERANCIA} m fuera de la calzada) de {len(con)} conectores")


if __name__ == "__main__":
    main()
