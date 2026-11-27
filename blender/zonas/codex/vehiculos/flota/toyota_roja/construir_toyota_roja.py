"""Reconstruye el vehículo medido en la lámina. Llamar con Blender en segundo plano."""
import json
import math
from pathlib import Path
import sys

import bpy

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[5]
sys.path.insert(0, str(RAIZ / ".agents/skills/vehiculo-3d-desde-diseno/scripts"))
from kit_vehiculo_bpy import (
    configurar_estudio_y_renderizar, configurar_normal_goma, consolidar_lotes,
    construir_ruedas_volumetricas, contorno_redondeado, crear_caja, crear_cilindro,
    crear_malla, crear_superficie_grid, crear_tubo, exportar_glb_vehiculo,
    inicializar_jerarquia, interpolar_hermite, material_pbr, preparar_rig_y_clips,
    suavizar_subsurf, validar_geometria_vehiculo,
)

SALIDA = RAIZ / "web/public/models/ciudad/codex/vehiculos/flota"
REVISION = RAIZ / "revisiones/codex/flota/toyota_roja"
DATOS = AQUI / "toyota_roja.json"


def intervalo(a, b, pasos):
    return [a + (b - a) * i / pasos for i in range(pasos + 1)]


def mezclar(a, b, t):
    return a + (b - a) * t


class Pickup:
    def __init__(self, datos):
        self.d = datos
        self.g = inicializar_jerarquia(datos["id"])
        self.m = {nombre: material_pbr(nombre, *valores) for nombre, valores in datos["paleta"].items()}
        pintura = self.m["pintura"].node_tree.nodes["Principled BSDF"]
        pintura.inputs["Specular IOR Level"].default_value = 0.28
        pintura.inputs["Coat Weight"].default_value = 0.13
        pintura.inputs["Coat Roughness"].default_value = 0.35
        vidrio = self.m["vidrio"].node_tree.nodes["Principled BSDF"]
        vidrio.inputs["Specular IOR Level"].default_value = 0.09
        vidrio.inputs["IOR"].default_value = 1.17
        self.perfiles = [list(zip((f[0] for f in datos["secciones"]), (f[i] for f in datos["secciones"])))
                         for i in (1, 2)]

    def grid(self, nombre, filas, mat="pintura", grupo="carroceria", **opciones):
        return crear_superficie_grid(nombre, filas, self.m[mat], self.g[grupo], **opciones)

    def tubo(self, nombre, puntos, radio, mat, cerrado=False, grupo="decoracion"):
        return crear_tubo(nombre, puntos, radio, self.m[mat], self.g[grupo], cerrado, resolucion=0)

    def bloque(self, nombre, centro, medidas, mat, bisel=0.012, grupo="interior"):
        return crear_caja(nombre, centro, medidas, self.m[mat], self.g[grupo], bisel)

    def cilindro(self, nombre, centro, radio, fondo, mat, eje="Y", grupo="interior"):
        return crear_cilindro(nombre, centro, radio, fondo, self.m[mat], self.g[grupo], eje=eje)

    def ancho(self, x):
        return interpolar_hermite(self.perfiles[0], x)

    def cintura(self, x):
        return interpolar_hermite(self.perfiles[1], x)

    def altura_paso(self, x):
        z = self.d["bajo"]
        bajo = interpolar_hermite([(-2.42, 0.834), (-2.35, 0.834), (-2.213, z),
                                   (2.174, z), (2.281, 0.938), (2.425, 0.938)], x)
        zc = self.d["centro_rueda_z"]
        for eje, radio in zip(self.d["ejes"], self.d["radio_paso"]):
            if abs(x - eje) < radio:
                bajo = max(bajo, zc + math.sqrt(radio**2 - (x - eje)**2))
        return bajo

    def chapa(self, x, z, lado, extra=0):
        """Barril de la chapa y aleta estampada alrededor de cada paso."""
        ancho, borde = self.ancho(x), self.cintura(x)
        h = z - borde
        perfil = [(-0.82, -0.089), (-0.69, -0.042), (-0.59, -0.022), (-0.49, -0.042),
                  (-0.40, -0.029), (-0.31, -0.008), (-0.15, 0.0), (-0.068, -0.004),
                  (-0.022, -0.022), (0.0, -0.051)]
        relieve = interpolar_hermite(perfil, h)
        for centro, radio in zip(self.d["ejes"], self.d["radio_paso"]):
            distancia = math.hypot(x - centro, z - self.d["centro_rueda_z"])
            relieve += 0.038 * math.exp(-((distancia - radio - 0.016) / 0.065) ** 2)
        return (x, lado * (ancho + relieve + extra), z)

    def piel(self):
        for lado in (-1, 1):
            for nombre, a, b in (("Costado estampado de caja", -2.42, -0.553),
                                  ("Costado de cabina y aleta delantera", -0.540, 2.425)):
                xs = set(intervalo(a, b, round((b - a) / 0.047)))
                xs.update(x for x in (-2.35, -2.213, 2.174, 2.281) if a < x < b)
                zc = self.d["centro_rueda_z"]
                for eje, radio in zip(self.d["ejes"], self.d["radio_paso"]):
                    corte = math.asin((self.d["bajo"] - zc) / radio)
                    xs.update(eje + radio * math.cos(t) for t in intervalo(corte, math.pi - corte, 38)
                              if a < eje + radio * math.cos(t) < b)
                filas = [[self.chapa(x, mezclar(self.altura_paso(x), self.cintura(x), t), lado)
                          for t in intervalo(0, 1, 16)] for x in sorted(xs)]
                self.grid(nombre, filas, invertir=lado == 1)
                self.grid("Canto inferior vuelto", [
                    [fila[0], (fila[0][0], fila[0][1] - lado * 0.026, fila[0][2] + 0.009)]
                    for fila in filas], invertir=lado == -1)
                extremo = filas[0 if a < -2 else -1]
                sentido = -1 if a < -2 else 1
                self.grid("Encuentro de la aleta con la cara transversal", [
                    [p, (self.cara_x(p[1] - lado * 0.039, sentido) - sentido * 0.013,
                         p[1] - lado * 0.039, p[2])] for p in extremo], invertir=lado == sentido)
            for eje, radio in zip(self.d["ejes"], self.d["radio_paso"]):
                corte = math.asin((self.d["bajo"] - zc) / radio)
                filas = []
                for t in intervalo(corte, math.pi - corte, 40):
                    x, z = eje + radio * math.cos(t), zc + radio * math.sin(t)
                    punto = self.chapa(x, z, lado, 0.001)
                    filas.append([punto, (x, lado * 0.482, z + 0.04), (x, lado * 0.480, zc - 0.035)])
                self.grid("Bóveda cerrada del guardabarros", filas, "oscuro", "interior", invertir=lado == 1)
                vivo = []
                for t in intervalo(corte, math.pi - corte, 55):
                    x, z = eje + (radio + 0.013) * math.cos(t), zc + (radio + 0.013) * math.sin(t)
                    if z >= self.altura_paso(x) - 0.005:
                        vivo.append(self.chapa(x, z, lado, 0.0047))
                self.tubo("Vivo metálico del paso", vivo, 0.008, "cromo")
            self.tubo("Hendidura longitudinal del estribo",
                      [self.chapa(x, 0.717, lado, 0.002) for x in intervalo(-0.52, 1.19, 42)],
                      0.004, "pintura_sombra")
            self.grafica(lado)

        def capo(x, v):
            y = (self.ancho(x) - 0.051) * v
            corona = 0.067 * (1 - abs(v)**3) * mezclar(0.85, 1.0, (x - 1.17) / 1.255)
            return (x, y, self.cintura(x) + corona)

        self.grid("Capó con hombros redondeados", [[capo(x, v) for v in intervalo(-1, 1, 32)]
                  for x in intervalo(1.170, 2.425, 38)])
        for lado in (-1, 1):
            self.tubo("Junta del capó", [(x, y, z + 0.003) for x, y, z in
                      (capo(x, lado * 0.849) for x in intervalo(1.219, 2.418, 42))],
                      0.0032, "pintura_sombra")
            self.grid("Umbral de ventanas de puerta", [
                [self.chapa(x, self.cintura(x), lado), (x, lado * self.cabina_y(x, self.cintura(x)),
                                                        self.cintura(x) + 0.002)]
                for x in intervalo(-0.54, 1.17, 36)], invertir=lado == 1)

    def grafica(self, lado):
        # Las dos tintas siguen el estampado al cambiar de panel.
        inferior = [(-2.38, 1.356), (-1.91, 1.29), (-1.19, 1.19), (-0.46, 1.075),
                    (0.28, 0.958), (0.91, 1.019), (1.28, 1.097), (1.70, 1.178), (2.18, 1.186)]
        superior = [(-2.38, 1.362), (-1.92, 1.353), (-1.26, 1.331), (-0.57, 1.302),
                    (-0.08, 1.270), (0.48, 1.202), (1.02, 1.116), (1.33, 1.118),
                    (1.79, 1.225), (2.18, 1.188)]
        division = [(-2.38, 0.55), (-0.52, 0.62), (0.29, 0.40), (0.91, 0.85), (2.18, 0.72)]
        for a, b in ((-2.38, -0.554), (-0.539, 2.18)):
            cortes = intervalo(a, b, round((b - a) / 0.033))
            for mat, n in (("grafica_gris", 0), ("grafica_plata", 1)):
                filas = []
                for x in cortes:
                    bajo = max(self.altura_paso(x) + 0.022, interpolar_hermite(inferior, x))
                    alto = max(bajo + 0.002, interpolar_hermite(superior, x))
                    medio = mezclar(bajo, alto, interpolar_hermite(division, x))
                    lim = (bajo, medio, alto)
                    filas.append([self.chapa(x, z, lado, 0.0026) for z in intervalo(lim[n], lim[n + 1], 5)])
                self.grid("Gráfica lateral " + mat, filas, mat, "decoracion", invertir=lado == 1)

    def cabina_y(self, x, z):
        c = self.d["cabina"]
        t = min(1, max(0, (z - self.cintura(x)) / (c["altura_lateral_techo"] - self.cintura(x))))
        return mezclar(self.ancho(x) - 0.074, c["ancho_techo"], t) + 0.023 * math.sin(math.pi * t)

    def cabina(self):
        c = self.d["cabina"]
        h = c["altura_lateral_techo"]
        bordes = [c[k] for k in ("borde_trasero", "pilar_central", "borde_delantero")]
        for lado in (-1, 1):
            def lado_cabina(p, offset=0):
                x, z = p
                return (x, lado * (self.cabina_y(x, z) + offset), z)

            for i, cristal in enumerate(c["ventanas_laterales"]):
                a, b = bordes[i:i + 2]
                exterior = [(a[0], self.cintura(a[0])), (b[0], self.cintura(b[0])),
                            (b[1], h), (a[1], h)]
                marco = densificar(contorno_redondeado(cristal, 0.041, 5), 3)
                borde = densificar(contorno_redondeado(exterior, 0, 5), 3)
                # Igual número de muestras en ambos contornos; los vértices repetidos
                # de las esquinas exteriores se limpian al soldar la superficie.
                anillo = [[lado_cabina(tuple(mezclar(p, q, t) for p, q in zip(e, m)))
                           for t in intervalo(0, 1, 5)] for e, m in zip(borde, marco)]
                self.grid("Chapa entre pilares y ventana", anillo, cerrar_u=True, invertir=lado == 1)
                puntos = [lado_cabina(p, 0.002) for p in marco]
                self.tubo("Burlete perimetral lateral", puntos, 0.014, "burlete", True)
                self.vidrio("Ventanilla de custodia" if i == 0 else "Cristal de puerta",
                            marco, lambda p: lado_cabina(p, -0.003))

            linea = [(0.10, 1.417), (0.114, 1.265), (0.114, 0.82), (0.131, 0.664), (0.186, 0.636),
                     (1.126, 0.640), (1.214, 0.687), (1.243, 0.924), (1.251, 1.282), (1.268, 1.365)]
            self.tubo("Junta de puerta", [self.chapa(x, z, lado, 0.008) for x, z in
                      densificar(contorno_redondeado(linea, 0.028, 4)[3:-4], 4, cerrado=False)],
                      0.0038, "pintura_sombra")
            self.accesorios_laterales(lado)

        a, b = bordes[0][1], bordes[-1][1]
        self.grid("Techo abovedado", [
            [(x + (0.026 * (1 - abs(v)**2) if i == 0 else
                   -0.018 * (1 - abs(v)**2) if i == 28 else 0),
              v * c["ancho_techo"], h + (1 - abs(v)**3) * (0.036 + 0.009 * math.sin(math.pi * i / 28)))
             for v in intervalo(-1, 1, 30)]
            for i, x in enumerate(intervalo(a, b, 28))])
        self.cierre_cabina("Parabrisas", bordes[-1], 1)
        self.cierre_cabina("Luneta corredera", bordes[0], -1)

    def vidrio(self, nombre, contorno, mapa):
        centro = tuple(sum(p[i] for p in contorno) / len(contorno) for i in (0, 1))
        filas = [[mapa(tuple(mezclar(a, b, t) for a, b in zip(centro, p))) for t in (0.10, 0.43, 0.76, 1)]
                 for p in contorno]
        self.grid(nombre, filas, "vidrio", "cristales", cerrar_u=True)
        crear_malla(nombre + " centro", [f[0] for f in filas], [tuple(range(len(filas)))],
                   self.m["vidrio"], self.g["cristales"])

    def cierre_cabina(self, nombre, extremos, sentido):
        h = self.d["cabina"]["altura_lateral_techo"]
        xb, xt = extremos
        zb = self.cintura(xb)
        wt = self.d["cabina"]["ancho_techo"]
        wb = self.cabina_y(xb, zb)

        def mapa(p, salida=0):
            u, v = p
            arco = 1 - abs(u)**2
            x = mezclar(xb, xt, v) + arco * mezclar(0.056 * sentido, -0.018 if sentido == 1 else 0.026, v)
            z = mezclar(zb, h, v) + arco * mezclar(0.016, 0.036, v)
            return (x + sentido * salida, u * mezclar(wb, wt, v) + u * 0.024 * math.sin(math.pi * v), z)

        def perimetro(ancho, base, alto, radio):
            p = [(-ancho, base), (ancho, base), (ancho, alto), (-ancho, alto)]
            radios = contorno_redondeado(p, radio, 5)
            return [tuple(mezclar(a, b, j / 3) for a, b in zip(v, radios[(i + 1) % len(radios)]))
                    for i, v in enumerate(radios) for j in range(3)]

        afuera = perimetro(1, 0, 1, 0)
        hueco = perimetro(0.902 if sentido == 1 else 0.866, 0.088, 0.906, 0.095)
        self.grid("Cintillo y marco de " + nombre, [
            [mapa(tuple(mezclar(a, b, t) for a, b in zip(p, q))) for t in intervalo(0, 1, 6)]
            for p, q in zip(afuera, hueco)], cerrar_u=True, invertir=sentido == -1)
        self.tubo("Burlete de " + nombre, [mapa(p, 0.003) for p in hueco], 0.013, "burlete", True)
        self.vidrio(nombre, hueco, lambda p: mapa(p, -0.006))
        if sentido == -1:
            for u in (-0.245, 0.245):
                self.tubo("Guía vertical de luneta", [mapa((u, v), 0.006) for v in intervalo(0.084, 0.905, 14)],
                          0.006, "burlete")
            return
        for u in (-0.52, 0.43):
            self.tubo("Brazo de limpiaparabrisas",
                      [mapa((u - 0.19, 0.087), 0.020), mapa((u - 0.14, 0.15), 0.023),
                       mapa((u + 0.055, 0.17), 0.023)], 0.009, "oscuro")
            self.tubo("Escobilla de limpiaparabrisas", [mapa((v, 0.17 - 0.10 * (v - u)), 0.019)
                      for v in intervalo(u - 0.16, u + 0.29, 13)], 0.012, "oscuro")

    def accesorios_laterales(self, lado):
        y = self.cabina_y(1.004, 1.474) * lado
        self.tubo("Pie de retrovisor", [(1.04, y * 0.98, 1.449), (1.022, y + lado * 0.083, 1.459),
                                       (0.987, y + lado * 0.142, 1.499)], 0.032, "oscuro")
        cuerpo = self.bloque("Carcasa de retrovisor", (0.974, y + lado * 0.143, 1.518),
                            (0.163, 0.253, 0.137), "oscuro", 0.041, "decoracion")
        suavizar_subsurf(cuerpo, 1)
        self.bloque("Cristal de retrovisor", (0.895, y + lado * 0.144, 1.519),
                    (0.010, 0.194, 0.095), "relieve_faro", 0.004, "decoracion")
        yy = self.chapa(0.296, 1.341, lado)[1]
        self.bloque("Cuenco de manilla", (0.296, yy, 1.338), (0.204, 0.026, 0.066), "burlete", 0.012, "decoracion")
        self.bloque("Manilla de puerta", (0.296, yy + lado * 0.015, 1.346),
                    (0.171, 0.025, 0.039), "cromo", 0.010, "decoracion")
        if lado == -1:
            perfil = contorno_redondeado([(-0.815, 1.007), (-0.634, 1.007), (-0.634, 1.186), (-0.815, 1.186)], 0.025)
            self.tubo("Junta de la tapa de combustible", [self.chapa(x, z, lado, 0.005) for x, z in perfil],
                      0.0036, "pintura_sombra", True)

    def caja_carga(self):
        caja = self.d["caja"]
        a, b, piso, ancho = (caja[k] for k in ("fondo", "frente", "piso", "ancho_interior"))
        for lado in (-1, 1):
            filas = []
            for x in intervalo(-2.42, b, 44):
                _, y, z = self.chapa(x, self.cintura(x), lado)
                filas.append([(x, y, z), (x, y - lado * 0.025, z + 0.012),
                              (x, lado * (ancho + 0.019), z + 0.007),
                              (x, lado * ancho, z - 0.024), (x, lado * ancho, piso)])
            self.grid("Baranda plegada y pared interior de caja", filas, invertir=lado == 1)
            self.tubo("Protector de borde de caja", [(f[1][0], (f[1][1] + f[2][1]) / 2, f[1][2] + 0.002)
                      for f in filas], 0.012, "burlete")
            self.bloque("Realce interior sobre el paso trasero", (-1.26, lado * 0.691, piso + 0.041),
                        (0.735, 0.161, 0.141), "pintura", 0.064)
        self.bloque("Piso de caja de carga", ((a + b) / 2, 0, piso - 0.022),
                    (b - a, ancho * 2, 0.048), "oscuro", 0.013)
        for y in intervalo(-0.61, 0.61, 10):
            self.bloque("Nervadura de piso de caja", ((a + b) / 2, y, piso + 0.004),
                        (b - a - 0.075, 0.028, 0.021), "burlete", 0.008)
        self.bloque("Mamparo delantero de caja", (b - 0.021, 0, 1.209),
                    (0.055, 1.627, 0.409), "pintura", 0.022, "carroceria")
        self.bloque("Mamparo trasero de cabina", (-0.523, 0, 1.002),
                    (0.042, 1.67, 0.77), "pintura_sombra", 0.021, "carroceria")
        self.bloque("Junta entre cabina y caja", (-0.548, 0, 1.021),
                    (0.014, 1.69, 0.759), "oscuro", 0.004, "carroceria")
        self.bloque("Cara interior del portón", (a + 0.007, 0, 1.201),
                    (0.041, 1.535, 0.401), "pintura", 0.017, "carroceria")
        self.tubo("Canto superior del portón", [(-2.422, y, 1.407 - 0.009 * abs(y))
                  for y in intervalo(-0.820, 0.820, 26)], 0.018, "burlete")

    def habitaculo(self):
        self.bloque("Bandeja inferior del habitáculo", (0.324, 0, 0.758), (1.67, 1.69, 0.21), "oscuro", 0.065)
        self.bloque("Tablero de instrumentos", (1.076, 0, 1.333), (0.39, 1.615, 0.223), "oscuro", 0.075)
        self.bloque("Capucha del cuadro de instrumentos", (1.017, 0.405, 1.469),
                    (0.236, 0.534, 0.088), "burlete", 0.037)
        self.bloque("Consola central", (0.60, 0, 0.995), (0.62, 0.205, 0.198), "burlete", 0.049)
        self.bloque("Banqueta de cabina extendida", (-0.262, 0, 1.050), (0.39, 1.37, 0.224), "tapizado", 0.068)
        for lado in (-1, 1):
            y = lado * 0.417
            self.bloque("Base de asiento", (0.37, y, 1.03), (0.51, 0.474, 0.195), "tapizado", 0.070)
            respaldo = self.bloque("Respaldo", (0.126, y, 1.304), (0.148, 0.444, 0.492), "tapizado", 0.066)
            respaldo.rotation_euler.y = -0.14
            for barra in (-0.068, 0.068):
                self.cilindro("Guía de apoyacabezas", (0.087, y + barra, 1.553), 0.010, 0.097, "cromo", "Z")
            self.bloque("Apoyacabezas", (0.079, y, 1.636), (0.112, 0.268, 0.17), "tapizado", 0.043)
            self.bloque("Panel interior de puerta", (0.449, lado * 0.779, 1.184),
                        (1.13, 0.106, 0.344), "tapizado", 0.048)
        self.tubo("Columna de dirección", [(1.022, 0.418, 1.247), (0.820, 0.418, 1.388)], 0.029, "oscuro")
        self.tubo("Aro del volante", [(0.814 + 0.071 * math.sin(t), 0.418 + 0.173 * math.cos(t),
                   1.396 + 0.159 * math.sin(t)) for t in intervalo(0, math.tau, 46)[:-1]],
                  0.016, "oscuro", True, "interior")
        self.bloque("Centro de volante", (0.808, 0.418, 1.392), (0.056, 0.180, 0.078), "burlete", 0.023)
        for signo in (-1, 1):
            self.tubo("Rayo de volante", [(0.812, 0.418, 1.383), (0.805, 0.418 + signo * 0.164, 1.373)],
                      0.019, "oscuro", grupo="interior")
        self.bloque("Retrovisor interior", (0.630, 0, 1.814), (0.058, 0.272, 0.090), "oscuro", 0.024)
        self.tubo("Anclaje del retrovisor interior", [(0.633, 0, 1.818), (0.687, 0, 1.852)],
                  0.014, "burlete", grupo="interior")
        self.bloque("Piso bajo capó", (1.777, 0, 0.981), (1.21, 1.05, 0.41), "oscuro", 0.055)
        self.bloque("Bastidor longitudinal", (0, 0, 0.642), (4.61, 0.954, 0.267), "oscuro", 0.048)
        for x in self.d["ejes"]:
            self.cilindro("Eje", (x, 0, self.d["centro_rueda_z"]), 0.064, 1.431, "oscuro")
            self.bloque("Cárter/diferencial", (x, 0, 0.443), (0.274, 0.285, 0.234), "burlete", 0.091)
            for lado in (-1, 1):
                xz = x - 0.524
                self.grid("Faldilla flexible de guardabarros",
                          [[(xz + 0.030 * (1 - u**2), lado * (0.794 + 0.150 * u), z)
                            for u in intervalo(-1, 1, 10)] for z in (0.284, 0.309, 0.48, 0.647)],
                          "oscuro", "interior")

    @staticmethod
    def cara_x(y, signo):
        if signo == 1:
            return 2.454 - 0.092 * (abs(y) / 0.92)**5
        return -2.447 + 0.057 * (abs(y) / 0.926)**5

    def placa_moldeada(self, nombre, y, z, w, h, signo, mat, salida=0, corona=0.011, radio=0.025,
                       estampado=None):
        esquinas = [(y - w / 2, z - h / 2), (y + w / 2, z - h / 2),
                    (y + w / 2, z + h / 2), (y - w / 2, z + h / 2)]
        contorno = contorno_redondeado(esquinas, radio, 3)
        contorno = [tuple(mezclar(a, b, j / 2) for a, b in zip(p, contorno[(i + 1) % len(contorno)]))
                    for i, p in enumerate(contorno) for j in range(2)]

        def punto(t, q, dz):
            yy, zz = mezclar(y, q[0], t), mezclar(z, q[1], t)
            return (self.cara_x(yy, signo) + signo * (salida + dz), yy, zz)

        perfil = estampado or ((1, -0.006), (1, 0), (0.94, corona * 0.8), (0.62, corona))
        filas = [[punto(t, q, dz) for t, dz in perfil] for q in contorno]
        self.grid(nombre, filas, mat, "decoracion", cerrar_u=True, invertir=signo == -1)
        crear_malla(nombre + " frente", [f[-1] for f in filas], [tuple(range(len(filas)))],
                   self.m[mat], self.g["decoracion"])

    def emblema(self, z, signo, escala, salida):
        for y0, z0, ry, rz in [(0, z, 0.095, 0.056), (0, z, 0.033, 0.052), (0, z + 0.022, 0.079, 0.019)]:
            self.tubo("Óvalo del emblema Toyota",
                      [(self.cara_x(0, signo) + signo * salida, y0 + escala * ry * math.cos(t),
                        z0 + escala * rz * math.sin(t)) for t in intervalo(0, math.tau, 36)[:-1]],
                      0.0045 * escala, "cromo", True)

    def defensa(self, signo):
        # Sección longitudinal de la defensa. El canto superior se recoge bajo
        # la chapa y el inferior vuelve hacia el bastidor.
        if signo == 1:
            perfil = [(0.934, -0.080), (0.918, 0.008), (0.888, 0.039), (0.844, 0.048),
                      (0.776, 0.038), (0.742, 0.011), (0.690, -0.036), (0.681, -0.103)]
        else:
            perfil = [(0.838, -0.080), (0.820, -0.008), (0.792, 0.032), (0.754, 0.048),
                      (0.678, 0.037), (0.652, -0.018), (0.640, -0.095)]

        def punto(u, z, vol):
            caida = abs(u)**6
            y = u * (0.920 - (0.014 if z < perfil[-3][0] else 0.001))
            # Mantiene holgura con el hombro del neumático durante todo el giro.
            despeje = caida * 0.103 if signo == 1 and z < 0.750 else 0
            return (self.cara_x(y, signo) + signo * (vol - 0.087 * caida + despeje), y, z + 0.006 * caida)

        filas = [[punto(u, z, vol) for z, vol in perfil] for u in intervalo(-1, 1, 56)]
        self.grid("Defensa cromada envolvente", [f[:6] for f in filas], "cromo", "carroceria", invertir=signo == 1)
        self.grid("Faldón recogido bajo la defensa", [f[5:] for f in filas], "oscuro", "carroceria",
                  invertir=signo == 1)
        for lado in (-1, 1):
            entrada = filas[0 if lado == -1 else -1]
            def retorno(p, t):
                remate = 0.043 if signo == 1 and p[2] < 0.754 else 0.083 if signo == 1 else 0.098
                return (p[0] - signo * remate * t,
                        p[1] + lado * (0.018 * math.sin(math.pi * t) - 0.027 * t**3), p[2])

            self.grid("Retorno superior de defensa", [[retorno(p, t) for p in entrada[:6]]
                      for t in intervalo(0, 1, 7)], "cromo", "carroceria", invertir=lado == signo)
            self.grid("Retorno del faldón", [[retorno(p, t) for p in entrada[5:]]
                      for t in intervalo(0, 1, 7)], "oscuro", "carroceria", invertir=lado == signo)

    def frente(self):
        s = 1
        self.grid("Panel frontal bajo el capó", [
            [(2.425, y, 1.208 + 0.067 * (1 - abs(u)**3)),
             (self.cara_x(y, s) - 0.010, y, 1.189), (self.cara_x(y, s) - 0.011, y, 0.905)]
            for u in intervalo(-1, 1, 40) for y in [u * 0.804]], invertir=True)
        self.placa_moldeada("Cerco de conjunto frontal", 0, 1.076, 1.740, 0.239, s, "cromo", 0.003, 0.003)
        self.placa_moldeada("Caja oscura de parrilla", 0, 1.075, 0.990, 0.199, s, "burlete", 0.007, 0.008)
        self.placa_moldeada("Fondo de toma superior", 0, 1.075, 0.945, 0.166, s, "oscuro", 0.013, 0.005)
        for z in (1.016, 1.053, 1.089, 1.129):
            self.placa_moldeada("Lama horizontal de parrilla", 0, z, 0.899, 0.015, s, "burlete", 0.019, 0.005, 0.007)
        self.emblema(1.079, s, 0.83, 0.041)
        for letra, puntos in (("V", [(-0.396, 1.041), (-0.377, 1.012), (-0.356, 1.042)]),
                               ("6", [(-0.313, 1.041), (-0.337, 1.042), (-0.345, 1.032),
                                      (-0.344, 1.014), (-0.315, 1.014), (-0.313, 1.029), (-0.343, 1.029)])):
            self.tubo("Insignia " + letra,
                      [(self.cara_x(y + 0.75, s) + 0.036, y + 0.75, z) for y, z in puntos], 0.0026, "cromo")
        for lado in (-1, 1):
            y = lado * 0.635
            self.placa_moldeada("Junta de óptica rectangular", y, 1.076, 0.269, 0.206, s, "burlete", 0.010)
            self.placa_moldeada("Lente convexa de faro rectangular", y, 1.076, 0.244, 0.182, s, "faro", 0.022, 0.014)
            self.placa_moldeada("Reflector central de faro", y, 1.084, 0.144, 0.106, s, "relieve_faro", 0.035, 0.008)
            self.placa_moldeada("Centro del reflector", y, 1.084, 0.092, 0.066, s, "faro", 0.042, 0.009)
            for dz in (-0.063, 0.065):
                self.tubo("Estría de lente", [(self.cara_x(v, s) + 0.040, v, 1.076 + dz)
                          for v in intervalo(y - 0.092, y + 0.092, 12)], 0.0026, "relieve_faro")
            self.placa_moldeada("Intermitente de esquina", lado * 0.815, 1.078, 0.089, 0.186, s, "ambar", 0.010)
        self.defensa(s)
        self.placa_moldeada("Marco de admisión inferior", 0, 0.804, 0.962, 0.159, s, "burlete", 0.049)
        self.placa_moldeada("Admisión inferior oscura", 0, 0.807, 0.894, 0.117, s, "oscuro", 0.058)
        self.placa_moldeada("Lama de admisión inferior", 0, 0.823, 0.852, 0.016, s, "burlete", 0.071)
        for lado in (-1, 1):
            y = lado * 0.671
            self.placa_moldeada("Junta de luz de defensa", y, 0.833, 0.247, 0.094, s, "oscuro", 0.033)
            self.placa_moldeada("Luz ámbar de defensa", y, 0.833, 0.215, 0.066, s, "ambar", 0.047)
        self.placa(s, 0.739)

    def placa(self, signo, z):
        self.placa_moldeada("Marco de matrícula", 0, z, 0.337, 0.167, signo, "burlete", 0.074, 0.009)
        self.placa_moldeada("Matrícula lisa", 0, z, 0.304, 0.139, signo, "matricula", 0.086, 0.007)
        for y in (-0.119, 0.119):
            self.cilindro("Fijación de matrícula", (self.cara_x(y, signo) + signo * 0.095, y, z + 0.047),
                          0.004, 0.008, "cromo", "X", "decoracion")

    def trasera(self):
        s = -1
        self.grid("Cierre trasero estructural", [
            [(self.cara_x(y, s) + 0.020, y, z) for z in (0.724, 0.86, 1.23, 1.387)]
            for y in intervalo(-0.867, 0.867, 44)])
        self.placa_moldeada("Junta de portón", 0, 1.119, 1.632, 0.558, s, "pintura_sombra", 0.000, 0.008)
        self.placa_moldeada("Portón con estampado hundido", 0, 1.124, 1.594, 0.526, s, "pintura",
                             0.015, radio=0.037, estampado=((1, -0.005), (1, 0), (0.954, 0.009),
                             (0.88, 0.014), (0.825, 0.014), (0.80, 0.004), (0.625, 0.004)))
        self.placa_moldeada("Encastre de manilla de caja", 0, 1.310, 0.234, 0.103, s, "oscuro", 0.033)
        self.placa_moldeada("Tirador de portón", 0, 1.321, 0.177, 0.041, s, "burlete", 0.050)
        self.emblema(1.133, s, 1.06, 0.025)
        self.defensa(s)
        self.placa_moldeada("Alojamiento de matrícula trasera", 0, 0.760, 0.565, 0.196, s, "oscuro", 0.049,
                             0.013, 0.046)
        self.placa(s, 0.750)
        for lado in (-1, 1):
            y = lado * 0.842
            self.placa_moldeada("Base de piloto vertical", y, 1.116, 0.158, 0.444, s, "burlete", 0.008)
            for z, h, mat in ((1.270, 0.124, "ambar"), (1.172, 0.061, "faro"), (1.023, 0.226, "rojo")):
                self.placa_moldeada("Lente trasera " + mat, y, z, 0.132, h, s, mat, 0.023, 0.014, 0.013)
            self.placa_moldeada("Reflector inferior de piloto", y, 0.961, 0.115, 0.042, s, "pintura_sombra", 0.041)

    def ruedas(self, ruta_goma):
        datos, m = self.d, self.m
        configurar_normal_goma(m["neumatico"], ruta_goma, 0.19)
        perfil = [(0.226, -0.111), (0.302, -0.126), (0.373, -0.136), (0.416, -0.130), (0.437, -0.113),
                  (0.444, -0.096), (0.445, -0.078), (0.445, -0.073), (0.437, -0.069), (0.437, -0.060),
                  (0.445, -0.056), (0.445, -0.022), (0.445, -0.008), (0.437, -0.005),
                  (0.437, 0.005), (0.445, 0.008), (0.445, 0.022), (0.445, 0.056),
                  (0.437, 0.060), (0.437, 0.069), (0.445, 0.073), (0.445, 0.078), (0.444, 0.096),
                  (0.437, 0.113), (0.416, 0.130), (0.373, 0.136), (0.302, 0.127), (0.226, 0.111)]
        llanta = [(0.018, 0.073), (0.083, 0.073), (0.116, 0.090), (0.173, 0.111), (0.192, 0.120),
                  (0.202, 0.133), (0.222, 0.135), (0.234, 0.126), (0.234, 0.108), (0.224, 0.090),
                  (0.224, -0.105), (0.204, -0.117), (0.192, -0.109), (0.181, 0.071),
                  (0.108, 0.064), (0.074, 0.053), (0.018, 0.053)]
        ventanas = [(a - 0.34, a + 0.34, 0.117, 0.183)
                    for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
        construir_ruedas_volumetricas(datos, m, self.g, perfil, llanta, segmentos_neumatico=72, segmentos_llanta=48,
                                     dibujo_banda=(0.438, 0.092, 0.003), ventanas_aleacion=ventanas,
                                     desp_agujero=0.097, n_tuercas=6, radio_tuercas=0.063,
                                     radio_buje=0.078, desp_buje=0.092)
        for nombre, pivote in self.g.items():
            if nombre.startswith("rueda_"):
                x, y, z = pivote.matrix_world.translation
                lado = math.copysign(1, y)
                self.cilindro("Disco de freno interior", (x, y + lado * 0.025, z), 0.183, 0.019,
                              "oscuro", grupo=nombre)
                for pieza in pivote.children:
                    if pieza.name.startswith("Tuerca rueda"):
                        pieza.location.y += lado * 0.009


def densificar(contorno, pasos, cerrado=True):
    siguientes = [*contorno[1:], contorno[0]] if cerrado else contorno[1:]
    puntos = [tuple(mezclar(a, b, j / pasos) for a, b in zip(p, q))
              for p, q in zip(contorno, siguientes) for j in range(pasos)]
    return puntos if cerrado else [*puntos, contorno[-1]]


def main(args=None):
    if args is None:
        args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.preferences.filepaths.save_version = 0
    datos = json.loads(DATOS.read_text())
    pickup = Pickup(datos)
    pickup.piel()
    pickup.cabina()
    pickup.caja_carga()
    pickup.habitaculo()
    pickup.frente()
    pickup.trasera()
    ruta_goma = AQUI.parents[1] / "texturas/Rubber004_1K-JPG_NormalGL.jpg"
    pickup.ruedas(ruta_goma)
    raiz = pickup.g["raiz"]
    movimiento = preparar_rig_y_clips(datos, pickup.g)
    bpy.context.view_layer.update()
    nombre = datos["id"]
    referencia = RAIZ / "autos/generadas" / (datos["referencia"] + "_diseno_miciudad.png")
    destinos = SALIDA if "--publicar" in args else REVISION
    destinos.mkdir(parents=True, exist_ok=True)

    # El maestro conserva piezas semánticas editables. Consolidar afecta
    # únicamente la copia de exportación en memoria.
    vistas = next((a.split("=", 1)[1].split(",") for a in args if a.startswith("--vistas=")), None)
    escena = bpy.context.scene
    escena.view_settings.view_transform = "AgX"
    escena.view_settings.look = "AgX - Medium High Contrast"
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type == "VIEW_3D":
                espacio = area.spaces.active
                espacio.region_3d.view_perspective = "CAMERA"
                espacio.shading.color_type = "MATERIAL"
                espacio.overlay.show_overlays = False
    configurar_estudio_y_renderizar(raiz, datos, destinos / (nombre + ".blend"),
                                    REVISION, vistas, referencia, sin_render=True)
    consolidar_lotes(raiz, ("neumatico",), "llanta")
    ficha = validar_geometria_vehiculo(raiz, datos, destinos / (nombre + ".ficha.json"), {
        "movimiento": movimiento, "referencia": datos["referencia"],
        "normal_goma": {"fuente": "ambientCG Rubber004", "licencia": "CC0 1.0"},
        "clips": ["rodar_adelante", "rodar_atras"]
    })
    print("FLOTA_VALIDACION", json.dumps(ficha, ensure_ascii=False), flush=True)
    exportar_glb_vehiculo(raiz, destinos / (nombre + ".glb"))
    if "--sin-render" not in args:
        bpy.ops.wm.open_mainfile(filepath=str(destinos / (nombre + ".blend")))
        escena = bpy.context.scene
        escena.cycles.samples = 20
        bpy.data.objects["ESTUDIO_suelo_no_exportado"].scale = (9, 9, 9)
        resoluciones = {"perspectiva": (1100, 760), "lateral": (1300, 620), "frente": (810, 800),
                        "trasera": (810, 800), "peaton": (1100, 760), "rueda": (880, 790)}
        for vista in vistas or resoluciones:
            escena.camera = bpy.data.objects["ESTUDIO_cam_" + vista]
            escena.camera.data.clip_end = 1500
            escena.render.resolution_x, escena.render.resolution_y = resoluciones[vista]
            escena.render.filepath = str(REVISION / (vista + ".png"))
            bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
