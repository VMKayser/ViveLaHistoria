"""Modelado de la Ford bicolor a partir de sus perfiles medidos."""
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

ID = "ford_azul"
SALIDA = RAIZ / "web/public/models/ciudad/codex/vehiculos/flota"
REVISION = RAIZ / "revisiones/codex/flota" / ID


def mezcla(a, b, t):
    return a + (b - a) * t


def muestras(a, b, n):
    return [mezcla(a, b, i / n) for i in range(n + 1)]


def densificar(puntos, pasos, cerrar=True):
    destinos = [*puntos[1:], puntos[0]] if cerrar else puntos[1:]
    densos = [tuple(mezcla(a, b, j / pasos) for a, b in zip(p, q))
              for p, q in zip(puntos, destinos) for j in range(pasos)]
    return densos if cerrar else [*densos, puntos[-1]]


def rectangulo(y, z, ancho, alto, radio, muestras_borde=2):
    w, h = ancho / 2, alto / 2
    esquinas = [(y - w, z - h), (y + w, z - h), (y + w, z + h), (y - w, z + h)]
    return densificar(contorno_redondeado(esquinas, radio, 3), muestras_borde)


class Ford:
    def __init__(self, datos):
        self.d = datos
        self.g = inicializar_jerarquia(ID)
        self.m = {n: material_pbr(n, *valores) for n, valores in datos["paleta"].items()}
        azul = self.m["azul_carroceria"].node_tree.nodes["Principled BSDF"]
        azul.inputs["Specular IOR Level"].default_value = 0.22
        azul.inputs["Coat Weight"].default_value = 0.08
        azul.inputs["Coat Roughness"].default_value = 0.32
        vidrio = self.m["vidrio"].node_tree.nodes["Principled BSDF"]
        vidrio.inputs["IOR"].default_value = 1.19
        vidrio.inputs["Specular IOR Level"].default_value = 0.12
        self.perfil_ancho = [(x, w) for x, w, z in datos["secciones"]]
        self.perfil_cintura = [(x, z) for x, w, z in datos["secciones"]]

    def superficie(self, nombre, filas, mat, grupo="carroceria", **opciones):
        return crear_superficie_grid(nombre, filas, self.m[mat], self.g[grupo], **opciones)

    def tubo(self, nombre, puntos, radio, mat, grupo="decoracion", cerrar=False):
        return crear_tubo(nombre, puntos, radio, self.m[mat], self.g[grupo], cerrar, resolucion=0)

    def bloque(self, nombre, pos, medidas, mat, bisel, grupo="interior"):
        return crear_caja(nombre, pos, medidas, self.m[mat], self.g[grupo], bisel)

    def cilindro(self, nombre, pos, radio, fondo, mat, eje="Y", grupo="interior"):
        return crear_cilindro(nombre, pos, radio, fondo, self.m[mat], self.g[grupo], eje=eje)

    def ancho(self, x):
        return interpolar_hermite(self.perfil_ancho, x)

    def cintura(self, x):
        return interpolar_hermite(self.perfil_cintura, x)

    def borde_inferior(self, x):
        return interpolar_hermite([(-2.49, 0.742), (-2.31, 0.746), (-2.105, 0.491),
                                  (2.135, 0.491), (2.257, 0.826), (2.462, 0.826)], x)

    def arco(self, x):
        minimo = self.borde_inferior(x)
        zc = self.d["centro_rueda_z"]
        for eje, radio in zip(self.d["ejes"], self.d["pasos_rueda"]):
            if abs(x - eje) < radio:
                minimo = max(minimo, zc + math.sqrt(radio**2 - (x - eje)**2))
        return minimo

    def chapa(self, x, z, lado, salida=0):
        h = z - self.cintura(x)
        panza = interpolar_hermite([(-0.98, -0.135), (-0.83, -0.092), (-0.67, -0.064),
                                   (-0.56, -0.055), (-0.47, -0.034), (-0.32, -0.024),
                                   (-0.18, -0.017), (-0.060, -0.019), (0, -0.058)], h)
        for eje, radio in zip(self.d["ejes"], self.d["pasos_rueda"]):
            distancia = math.hypot(x - eje, z - self.d["centro_rueda_z"])
            panza += 0.078 * math.exp(-((distancia - radio - 0.077) / 0.095)**2)
        return x, lado * (self.ancho(x) + panza + salida), z

    def carroceria(self):
        alto_zocalo = [(-2.49, 0.753), (-1.935, 0.733), (-0.968, 0.751), (-0.78, 0.644),
                       (1.057, 0.644), (1.231, 0.756), (2.462, 0.818)]
        for lado in (-1, 1):
            cortes = [(-2.49, -1.088), (-1.064, 2.462)]
            for inicio, fin in cortes:
                xs = set(muestras(inicio, fin, round((fin - inicio) / 0.060)))
                for eje, radio in zip(self.d["ejes"], self.d["pasos_rueda"]):
                    xs.update(eje + radio * math.cos(t) for t in muestras(0.10, math.pi - 0.10, 34)
                              if inicio < eje + radio * math.cos(t) < fin)
                orden = sorted(xs)
                def franjas(x):
                    base = self.arco(x)
                    return base, max(base, interpolar_hermite(alto_zocalo, x)), self.cintura(x)

                filas = [[self.chapa(x, z, lado) for z in muestras(franjas(x)[1], franjas(x)[2], 12)]
                         for x in orden]
                self.superficie("Costado con aletas estampadas", filas, "azul_carroceria", invertir=lado == 1)
                faldon = [[self.chapa(x, z, lado) for z in muestras(franjas(x)[0], franjas(x)[1], 4)] for x in orden]
                self.superficie("Zócalo bicolor recortado", faldon, "gris_champan", invertir=lado == 1)
                self.superficie("Canto de chapa inferior",
                    [[f[0], (f[0][0], f[0][1] - lado * 0.028, f[0][2] + 0.008)] for f in faldon],
                    "oscuro", invertir=lado == -1)
                extremo = (0 if inicio < -2 else -1)
                signo = -1 if extremo == 0 else 1
                cara = faldon[extremo][:-1] + filas[extremo]
                self.superficie("Encuentro redondeado de aleta y fascia",
                    [[p, (self.cara_x(p[1] - lado * .037, p[2], signo) - signo * .018,
                          p[1] - lado * .037, p[2])] for p in cara],
                    "azul_carroceria", invertir=lado == signo)

            for eje, radio in zip(self.d["ejes"], self.d["pasos_rueda"]):
                zc = self.d["centro_rueda_z"]
                arco = [(eje + radio * math.cos(t), zc + radio * math.sin(t))
                        for t in muestras(0.10, math.pi - 0.10, 46)]
                visibles = [(x, z) for x, z in arco if z >= self.borde_inferior(x) - .003]
                interior = .480 if eje > 0 else .567
                self.superficie("Bóveda del guardabarros", [
                    [self.chapa(x, z, lado), (x, lado * interior, z + .074),
                     (x, lado * (interior-.006), zc - .018)]
                    for x, z in visibles], "oscuro", "interior", invertir=lado == 1)
                self.superficie("Labio vuelto de aleta",
                    [[self.chapa(x, z, lado), self.chapa(x, z + .012, lado, .009),
                      self.chapa(x, z + .031, lado, .007)] for x, z in visibles],
                    "azul_molduras", invertir=lado == -1)
            self.molduras_puertas(lado)

        self.superficie("Capó abombado con doble nervadura",
            [[self.capo(x, u) for u in muestras(-1, 1, 34)] for x in muestras(1.103, 2.462, 35)],
            "azul_carroceria")
        for lado in (-1, 1):
            self.tubo("Junta de capó", [(x, y, z + .002) for x, y, z in
                      (self.capo(x, lado * .768) for x in muestras(1.167, 2.436, 39))], .0035, "oscuro")

    def capo(self, x, u):
        hombro = 1 - abs(u)**3
        centro = .046 * hombro + .023 * math.exp(-((abs(u) - .45) / .16)**2) * hombro
        return x, (self.ancho(x) - .058) * u, self.cintura(x) + centro

    def molduras_puertas(self, lado):
        contornos = [
            [(-1.048,1.403),(-.928,.999),(-.828,.673),(-.692,.642),(.075,.642),(.119,.717),(.105,1.362)],
            [(.122,1.369),(.116,.709),(.163,.643),(1.025,.643),(1.102,.691),(1.139,1.351)]
        ]
        for linea in contornos:
            puntos = densificar(contorno_redondeado(linea, .05, 4)[3:-4], 6, False)
            self.tubo("Junta de puerta", [self.chapa(x, z, lado, .0065) for x, z in puntos],
                      .0039, "oscuro")
        for a, b in ((-.878, .090), (.136, 1.104)):
            self.superficie("Moldura ancha de protección", [
                [self.chapa(x, z, lado, ext * max(.08, min(1, (x-a)*45, (b-x)*45)))
                 for z, ext in ((.849,.001),(.865,.019),(.913,.022),(.936,.006))]
                for x in muestras(a, b, 24)], "azul_molduras", invertir=lado == 1)
            self.tubo("Vivo de la moldura", [self.chapa(x, .921, lado, .022)
                      for x in muestras(a + .036, b - .036, 22)], .0046, "aluminio")
        for x in (-.722, .318):
            y = self.chapa(x, 1.292, lado)[1]
            self.bloque("Cazoleta de manilla", (x,y,1.294), (.191,.030,.078), "oscuro", .024, "decoracion")
            self.bloque("Accionador de puerta", (x,y+lado*.016,1.307), (.158,.025,.035),
                        "azul_molduras", .013, "decoracion")
        self.cilindro("Cerradura de puerta", (.318,self.chapa(.318,1.214,lado,.006)[1],1.214),
                      .011,.009,"aluminio", grupo="decoracion")

        # Tubo de estribo con extremos curvos, pasaderas altas y soportes al chasis.
        perfil = [(-.943,.849,.384),(-.908,.904,.386),(-.838,.984,.388),(-.734,1.017,.388),
                  (1.003,1.017,.388),(1.092,.997,.393),(1.157,.935,.411),(1.190,.885,.442)]
        self.tubo("Estribo tubular", [(x, lado*y, z) for x,y,z in densificar(perfil,3,False)],
                  .049, "gris_champan", "carroceria")
        for x in (-.527,.576):
            self.bloque("Pasadera de goma", (x,lado*1.019,.427),(.495,.154,.027), "burlete", .012, "decoracion")
            self.bloque("Soporte al larguero", (x,lado*.830,.38),(.101,.368,.070), "oscuro", .017)

    def ancho_cabina(self, x, z):
        c = self.d["cabina"]
        h = self.cintura(x)
        t = max(0, min(1, (z - h) / (c["altura_lateral_techo"] - h)))
        return mezcla(self.ancho(x) - .076, c["ancho_lateral_techo"], t) + .038 * math.sin(math.pi * t)

    def junta_y_cristal(self, nombre, exterior, hueco, mapa, invertir=False):
        centro = [sum(p[i] for p in hueco) / len(hueco) for i in (0, 1)]
        self.superficie("Chapa y pilares " + nombre,
            [[mapa(tuple(mezcla(a,b,t) for a,b in zip(e,c))) for t in muestras(0,1,5)]
             for e,c in zip(exterior,hueco)], "azul_carroceria", cerrar_u=True, invertir=invertir)
        self.tubo("Burlete " + nombre, [mapa(v,.0015) for v in hueco], .014, "burlete", cerrar=True)
        filas = [[mapa(tuple(mezcla(a,b,t) for a,b in zip(centro,p)), -.006)
                  for t in (.2,.56,.80,1)] for p in hueco]
        self.superficie("Cristal " + nombre, filas, "vidrio", "cristales", cerrar_u=True, invertir=invertir)
        self.tapa("Paño central " + nombre, [f[0] for f in filas], "vidrio", "cristales", invertir)

    def tapa(self, nombre, puntos, mat, grupo, invertir=False):
        cara = tuple(range(len(puntos)))
        crear_malla(nombre, puntos, [cara[::-1] if invertir else cara], self.m[mat], self.g[grupo])

    def cabina(self):
        datos = self.d["cabina"]
        a, b, c = datos["bordes"]
        h, w = datos["altura_lateral_techo"], datos["ancho_lateral_techo"]
        for lado in (-1, 1):
            def lateral(p, relieve=0):
                x,z = p
                return x, lado*(self.ancho_cabina(x,z)+relieve), z

            for i, (borde, siguiente) in enumerate(((a,b),(b,c))):
                x0,t0 = borde
                x1,t1 = siguiente
                marco = [(x0,self.cintura(x0)),(x1,self.cintura(x1)),(t1,h),(t0,h)]
                def muestrear_bordes(contorno):
                    return [tuple(mezcla(p,q,t) for p,q in zip(v,contorno[(j+1)%len(contorno)]))
                            for j,v in enumerate(contorno)
                            for t in muestras(0,1,14 if j in (4,14) else 4 if j in (9,19) else 1)[:-1]]
                exterior = muestrear_bordes(contorno_redondeado(marco,0,4))
                z0,z1 = self.cintura(x0),self.cintura(x1)
                exterior = [(x,self.cintura(x) if abs(z-mezcla(z0,z1,(x-x0)/(x1-x0))) < .001 else z)
                            for x,z in exterior]
                hueco = muestrear_bordes(contorno_redondeado(datos["ventanas"][i],.049,4))
                nombre = "puerta trasera" if i == 0 else "puerta delantera"
                self.junta_y_cristal(nombre,exterior,hueco,lateral,invertir=lado==1)
                if i == 0:
                    self.tubo("Divisor negro de cristal fijo trasero",
                        [lateral((x,z),.001) for x,z in zip(muestras(-.680,-.644,16),muestras(1.421,1.898,16))],
                        .015,"burlete")
            self.superficie("Vierteaguas bajo cristales de puerta",[
                [self.chapa(x,self.cintura(x),lado),lateral((x,self.cintura(x)),.002)] for x in muestras(a[0],1.105,46)],
                "azul_carroceria",invertir=lado==-1)
            self.tubo("Vivo superior lateral del cristal",[
                lateral((x,h-.013),.002) for x in muestras(a[1]+.012,c[1]-.015,32)], .003,"azul_molduras")
            self.retrovisor(lado)

        def cubierta(i,u):
            t = i/28
            x = mezcla(a[1],c[1],t)
            curvatura = 1-u*u
            x += curvatura*(.039 if i==0 else -.022 if i==28 else 0)
            z = h + curvatura*(.050 + .012*math.sin(math.pi*t))
            return x,w*u,z

        self.superficie("Techo de hombros curvos",[[cubierta(i,u) for u in muestras(-1,1,30)]
            for i in range(29)],"azul_carroceria")
        self.cierre_transversal("parabrisas",c,1)
        self.cierre_transversal("luneta",a,-1)
        for lado in (-1,1):
            perfil = [(-.744,.546,1.970),(-.685,.554,2.019),(-.584,.553,2.030),(-.424,.552,2.031),
                      (.454,.549,2.031),(.535,.539,2.011),(.559,.529,1.967)]
            puntos = [(x,lado*y,z) for x,y,z in densificar(perfil,4,False)]
            self.tubo("Riel longitudinal de techo",puntos,.027,"burlete","carroceria")
            self.tubo("Alma de aluminio del riel",[(x,lado*.553,2.050) for x in muestras(-.563,.422,30)],
                .008,"aluminio")
        self.bloque("Carcasa de luz de freno alta",(-.834,0,1.938),(.051,.291,.057),"oscuro",.016,"decoracion")
        self.bloque("Tercera luz de freno",(-.863,0,1.939),(.017,.268,.040),"rojo",.010,"decoracion")

    def cierre_transversal(self,nombre,linea,signo):
        x0,x1 = linea
        z0,h = self.cintura(x0),self.d["cabina"]["altura_lateral_techo"]
        w0,w1 = self.ancho_cabina(x0,z0),self.d["cabina"]["ancho_lateral_techo"]
        def mapa(p, salida=0):
            u,v = p
            arco = 1-u*u
            x = mezcla(x0,x1,v) + arco*mezcla(signo*.055,-.022 if signo==1 else .039,v)
            y = u*(mezcla(w0,w1,v)+.039*math.sin(math.pi*v))
            z = mezcla(z0,h,v)+arco*mezcla(.024,.05,v)
            return x+signo*salida,y,z

        exterior = rectangulo(0,.5,2,1,0,4)
        hueco = rectangulo(0,.49,1.79 if signo==1 else 1.76,.810,.114,4)
        self.junta_y_cristal(nombre,exterior,hueco,mapa,invertir=signo<0)
        if signo > 0:
            for u in (-.50,.39):
                self.tubo("Brazo del limpiaparabrisas",[mapa((u-.20,.079),.019),
                    mapa((u-.127,.142),.023),mapa((u+.046,.171),.023)],.010,"oscuro")
                self.tubo("Escobilla",[mapa((v,.171-.080*(v-u)),.019)
                    for v in muestras(u-.147,u+.294,15)], .012,"oscuro")

    def retrovisor(self,lado):
        x,z = .923,1.507
        y = lado*self.ancho_cabina(x,z)
        self.tubo("Pie de retrovisor",[(x+.044,y,1.462),(x+.016,y+lado*.092,1.475),
                                     (x-.018,y+lado*.141,1.53)],.044,"oscuro")
        carcasa = self.bloque("Carcasa de retrovisor", (x-.028,y+lado*.156,z+.014),(.207,.259,.164),
                             "oscuro",.061,"decoracion")
        suavizar_subsurf(carcasa,1)
        self.bloque("Espejo convexo", (x-.133,y+lado*.154,z+.012),(.013,.195,.103),
                    "relieve_faro",.006,"decoracion")

    def caja_cerrada(self):
        d = self.d["caja"]
        a,b,w,z = (d[k] for k in ("fondo","frente","lateral","altura"))
        for lado in (-1,1):
            self.superficie("Borde estampado de la caja corta",[
                [self.chapa(x,self.cintura(x),lado),(x,lado*(w+.030),self.cintura(x)+.016),
                 (x,lado*w,z-.019)] for x in muestras(-2.488,b,32)],
                "azul_carroceria",invertir=lado==1)
            self.tubo("Riel de la cubierta de caja",[(x,lado*w,z-.017) for x in muestras(a,b,25)],
                      .022,"burlete","carroceria")
            for x in (-2.141,-1.582):
                self.bloque("Anclaje exterior de cubierta",(x,self.chapa(x,1.408,lado)[1],1.408),
                            (.129,.043,.039),"burlete",.011,"decoracion")
        self.superficie("Tapa cerrada de caja con caída lateral",[
            [(x,w*u,z-.023+.028*(1-u*u)*math.sin(math.pi*(x-a+.14)/(b-a+.28)))
             for u in muestras(-1,1,22)] for x in muestras(a,b,28)],"oscuro","carroceria")
        for x in muestras(a+.080,b-.070,9):
            self.tubo("Junta discreta de la cubierta",[(x,u*w,z-.020+.028*(1-u*u)*math.sin(math.pi*(x-a+.14)/(b-a+.28)))
                       for u in muestras(-.963,.963,18)], .0022, "burlete")
        self.bloque("Mamparo de cabina bajo luneta",(-1.047,0,1.095),(.063,1.71,.708),"azul_carroceria",.022,"carroceria")

    def interiores(self):
        self.bloque("Piso cerrado de doble cabina",(.031,0,.744),(2.16,1.729,.231),"oscuro",.064)
        self.bloque("Tablero acolchado",(.972,0,1.336),(.53,1.637,.208),"oscuro",.093)
        self.bloque("Visera de tablero",(.854,.433,1.458),(.22,.487,.087),"burlete",.036)
        self.bloque("Consola y apoyabrazos delanteros",(.369,0,1.051),(.55,.287,.233),"burlete",.059)
        self.bloque("Banqueta posterior",(-.639,0,.989),(.547,1.444,.222),"tapizado",.061)
        respaldo = self.bloque("Respaldo posterior",(-.816,0,1.232),(.162,1.435,.443),"tapizado",.066)
        respaldo.rotation_euler.y = -.13
        for lado in (-1,1):
            y = .412*lado
            for x in (-.850,.087):
                self.bloque("Apoyacabezas",(x,y,1.625 if x>0 else 1.526),(.129,.244,.169),
                            "tapizado",.049)
            self.bloque("Cojín delantero",(.286,y,1.004),(.500,.484,.202),"tapizado",.073)
            respaldo = self.bloque("Respaldo delantero",(.062,y,1.273),(.165,.444,.474),"tapizado",.065)
            respaldo.rotation_euler.y = -.16
            for x in (-.456,.585):
                self.bloque("Panel interior de puerta",(x,lado*.801,1.133),(.881,.168,.352),
                            "tapizado",.075)
        self.tubo("Volante de cuatro brazos",[(.738+.064*math.sin(t),.418+.166*math.cos(t),
                   1.382+.162*math.sin(t)) for t in muestras(0,math.tau,36)[:-1]],
                  .019,"oscuro","interior",True)
        self.bloque("Mando central del volante",(.752,.417,1.377),(.082,.238,.102),"burlete",.034)
        self.tubo("Columna de dirección",[(.752,.418,1.388),(1.017,.418,1.259)],.045,"oscuro","interior")
        self.bloque("Espejo interior",(.576,0,1.816),(.064,.304,.078),"oscuro",.030)
        self.tubo("Pie de espejo interior",[(.58,0,1.82),(.653,0,1.864)],.016,"oscuro","interior")
        self.bloque("Bastidor longitudinal",(-.010,0,.560),(4.66,1.029,.286),"oscuro",.061)
        self.bloque("Bandeja baja bajo el capó",(1.767,0,.957),(1.32,1.13,.358),"oscuro",.065)
        for x in self.d["ejes"]:
            self.cilindro("Travesaño de eje",(x,0,.447),.066,1.51,"oscuro")
            self.bloque("Diferencial",(x,0,.432),(.271,.339,.245),"burlete",.078)
        for lado in (-1,1):
            self.superficie("Faldilla de goma posterior",[
                [(-2.027-.014*(1-u*u),lado*(.826+.163*u),z) for u in muestras(-1,1,9)]
                for z in (.276,.321,.498,.699)],"oscuro","interior")

    @staticmethod
    def cara_x(y,z,signo):
        if signo > 0:
            perfil = [(.426,2.383),(.495,2.462),(.594,2.537),(.718,2.554),(.817,2.503),
                      (.896,2.477),(1.163,2.484),(1.207,2.471),(1.301,2.409)]
            esquina = .115
        else:
            perfil = [(.407,-2.405),(.448,-2.486),(.510,-2.544),(.645,-2.555),(.738,-2.512),
                      (.791,-2.494),(1.427,-2.506),(1.508,-2.473)]
            esquina = .082
        return interpolar_hermite(perfil,z) - signo*esquina*(abs(y)/.975)**5

    def cara(self,p,signo,ext=0):
        y,z = p
        return self.cara_x(y,z,signo)+signo*ext,y,z

    def relieve(self,nombre,contorno,signo,mat,ext=0,curva=.012):
        centro = tuple(sum(p[i] for p in contorno)/len(contorno) for i in (0,1))
        filas = [[self.cara(tuple(mezcla(c,x,t) for c,x in zip(centro,p)),signo,ext+avance)
                  for t,avance in ((1,-.011),(1,0),(.95,curva*.7),(.80,curva))] for p in contorno]
        self.superficie(nombre,filas,mat,"decoracion",cerrar_u=True,invertir=signo<0)
        self.tapa(nombre+" paño",[f[-1] for f in filas],mat,"decoracion",invertir=signo<0)

    def pieza_frontal(self,nombre,y,z,w,h,signo,mat,ext=0,curva=.010,radio=.028):
        self.relieve(nombre,rectangulo(y,z,w,h,radio),signo,mat,ext,curva)

    def defensa(self,signo):
        alto = .817 if signo>0 else .738
        bajo = .445 if signo>0 else .418
        def mapa(p,extra=0):
            y,v = p
            z = mezcla(bajo,alto,v)
            if signo>0:
                z -= .067 * (abs(y)/.969)**8 * v**3
            else:
                z += .012*(abs(y)/.969)**3*(1-v)
            return self.cara((y,z),signo,extra)

        # Cada paño tiene un hueco real en la piel de la defensa, con pared de retorno.
        limites = [-.969,-.555,.555,.969]
        vertices,caras,indices = [],[],{}
        for i,(l,r) in enumerate(zip(limites,limites[1:])):
            y = (l+r)/2
            exterior = [(yy,0) for yy in muestras(l,r,16)[:-1]] + [
                (r,v) for v in muestras(0,1,14)[:-1]] + [(yy,1) for yy in muestras(r,l,16)[:-1]] + [
                (l,v) for v in muestras(1,0,14)[:-1]]
            vc, vh = (.437,.235) if signo>0 else (.437,.368)
            if i==1:
                ancho = .511 if signo>0 else .307
                centro, exponente = 0, .36
            elif signo>0:
                ancho, vh, centro, vc, exponente = .103,.281,y,.495,1
            else:
                self.acumular_piel(vertices,caras,indices,
                    [[mapa((yy,v)) for v in muestras(0,1,14)] for yy in muestras(l,r,20)], signo<0)
                continue
            interior = []
            for yy,v in exterior:
                t = math.atan2((v-vc)/vh,(yy-centro)/ancho)
                c,s = math.cos(t), math.sin(t)
                interior.append((centro+ancho*math.copysign(abs(c)**exponente,c),
                                 vc+vh*math.copysign(abs(s)**exponente,s)))
            filas = [[mapa(tuple(mezcla(a,b,t) for a,b in zip(p,q))) for t in muestras(0,1,5)]
                     for p,q in zip(exterior,interior)]
            self.acumular_piel(vertices,caras,indices,[*filas,filas[0]],signo<0)
            bordes = [[mapa(p),mapa(p,-.021),mapa(p,-.058)] for p in interior]
            self.superficie("Retorno de la cavidad de defensa",bordes,"gris_champan",cerrar_u=True,invertir=signo>0)
            self.tapa("Fondo de la cavidad en sombra",[f[-1] for f in bordes],"oscuro","carroceria",invertir=signo<0)

        for lado in (-1,1):
            def esquina(v,t):
                p = mapa((lado*.969,v))
                x = mezcla(2.226,2.236,v) if signo>0 else mezcla(-2.138,-2.114,v)
                z = mezcla(.519,.825,v) if signo>0 else mezcla(.493,.744,v)
                y = self.chapa(x,z,lado,.012)[1]
                return (mezcla(p[0],x,t), mezcla(p[1],y,t*t)+lado*.012*math.sin(math.pi*t),
                        mezcla(p[2],z,t))
            self.acumular_piel(vertices,caras,indices,[[esquina(v,t) for v in muestras(0,1,14)]
                            for t in muestras(0,1,9)],lado==signo)
            techo_ala = [esquina(1,t) for t in muestras(0,1,9)]
            self.acumular_piel(vertices,caras,indices,[
                [p,(p[0],p[1]-lado*.041,p[2]+.018)] for p in techo_ala],lado==signo)
            remate = [esquina(v,1) for v in muestras(0,1,14)]
            self.acumular_piel(vertices,caras,indices,[
                [p,(p[0]+signo*.011,p[1]-lado*.068,p[2]-.008)] for p in remate],lado!=signo)
            self.superficie("Faldón bajo defensa",[
                [mapa((lado*u,0)),(mapa((lado*u,0))[0]-signo*.102,lado*u*.968,bajo-.019)]
                for u in muestras(0,.969,30)],"oscuro",invertir=lado==signo)
            if signo>0:
                f = mapa((lado*.762,.490),-.047)
                self.cilindro("Foco auxiliar hundido",f,.061,.018,"burlete","X","decoracion")
            else:
                x,y,z = mapa((lado*.734,.646),.003)
                self.cilindro("Punto de sensor posterior",(x,y,z),.023,.014,"burlete","X","decoracion")
        crear_malla("Piel continua de defensa " + ("delantera" if signo>0 else "trasera"),
                    vertices,caras,self.m["gris_champan"],self.g["carroceria"],suavizar=True)
        if signo>0:
            self.superficie("Franja azul solidaria con el parachoques",[
                [mapa((y,1),-.008),(self.cara_x(y,.859,1)-.023,y,.869),
                 (self.cara_x(y*.922,.901,1)-.018,y*.922,.901)]
                for y in muestras(-.969,.969,42)],"azul_carroceria",invertir=True)
        p = mapa((0,.51),-.024 if signo < 0 else .023)
        self.placa(p,signo)

    @staticmethod
    def acumular_piel(vertices,caras,indices,filas,invertir):
        """Une costuras entre paños de la defensa para compartir las normales."""
        rejilla = []
        for fila in filas:
            ids = []
            for v in fila:
                clave = tuple(round(c,7) for c in v)
                if clave not in indices:
                    indices[clave] = len(vertices)
                    vertices.append(v)
                ids.append(indices[clave])
            rejilla.append(ids)
        for a,b in zip(rejilla,rejilla[1:]):
            for i in range(len(a)-1):
                q = (a[i],b[i],b[i+1],a[i+1])
                caras.append(q[::-1] if invertir else q)

    def placa(self,p,signo):
        x,y,z = p
        self.bloque("Soporte de matrícula",p,(.053,.400,.198),"burlete",.016,"decoracion")
        self.bloque("Placa sin inscripción",(x+signo*.033,y,z),(.020,.351,.161),"placa",.010,"decoracion")
        for yy in (-.142,.142):
            self.cilindro("Remache de matrícula",(x+signo*.045,yy,z+.066),.0043,.008,
                          "aluminio","X","decoracion")

    def emblema(self,z,signo,ext,escala=1):
        x = self.cara_x(0,z,signo)+signo*ext
        marco = [(x,escala*.095*math.cos(t),z+escala*.039*math.sin(t)) for t in muestras(0,math.tau,44)[:-1]]
        self.tapa("Centro azul del emblema Ford",marco,"azul_emblema","decoracion",invertir=signo<0)
        self.tubo("Borde aluminio del óvalo Ford",marco,.005,"aluminio",cerrar=True)
        trazos = [
            [(-.063,.013),(-.029,.016),(-.038,.019),(-.052,.011),(-.052,-.004),(-.059,-.014),(-.067,-.012)],
            [(-.062,.000),(-.033,.003)],
            [(-.031,.004),(-.040,-.003),(-.040,-.012),(-.031,-.016),(-.020,-.009),(-.019,-.001),(-.027,.005),(-.031,.004)],
            [(-.020,-.008),(-.010,.003),(-.007,-.007),(-.001,.003),(.004,.004)],
            [(.025,.002),(.012,.003),(.002,-.006),(.005,-.014),(.015,-.014),(.024,-.004),(.039,.017),
             (.029,.006),(.024,-.011),(.032,-.014),(.043,-.006),(.051,.002),(.061,.004)]
        ]
        for trazo in trazos:
            self.tubo("Trazo cursivo del óvalo",
                      [(x+signo*.002,signo*escala*y,z+escala*zz) for y,zz in trazo],.0016,"aluminio")

    def frontal(self):
        self.superficie("Nariz continua bajo el capó",[
            [self.capo(2.462,u), self.cara((y,1.196),1,-.016),
             self.cara((y,.875),1,-.022)] for u in muestras(-1,1,34) for y in [u*.816]],
            "azul_carroceria",invertir=True)
        esquinas = [(-.390,.916),(.390,.916),(.421,1.198),(-.421,1.198)]
        parrilla = densificar(contorno_redondeado(esquinas,.046,5),3)
        self.relieve("Cerco trapezoidal de parrilla",parrilla,1,"azul_molduras",.003,.011)
        fondo = densificar(contorno_redondeado([(-.363,.940),(.363,.940),(.386,1.170),(-.386,1.170)],.021,4),3)
        self.relieve("Fondo de parrilla negra",fondo,1,"oscuro",.014,.009)
        # Malla a rombos, recortada en la planta trapezoidal y pegada al frente curvo.
        segmentos = (1,-1)
        for orientacion in segmentos:
            for y in muestras(-.494,.494,37):
                puntos = []
                for t in muestras(0,1,8):
                    v = y + orientacion*.147*(t-.5)
                    if abs(v) <= mezcla(.351,.376,t):
                        puntos.append(self.cara((v,mezcla(.946,1.163,t)),1,.024))
                if len(puntos)>1:
                    self.tubo("Nervio de rejilla de rombos",puntos,.0018,"rejilla")
        self.pieza_frontal("Barra central de parrilla",0,1.054,.724,.027,1,"azul_molduras",.030,.012,.010)
        self.emblema(1.052,1,.045,.91)
        for lado in (-1,1):
            def reflejar(perfil):
                return densificar(contorno_redondeado([(lado*y,z) for y,z in perfil],.026,3),2)

            toma = [(.420,.932),(.474,.934),(.525,1.183),(.451,1.183)]
            self.relieve("Ranura vertical junto a parrilla",reflejar(toma),1,"oscuro",.012,.011)
            borde_faro = [(.478,.938),(.934,.939),(.922,1.160),(.542,1.181)]
            self.relieve("Marco envolvente de óptica",reflejar(borde_faro),1,"azul_molduras",.009,.013)
            lente = [(.510,.953),(.816,.953),(.802,1.143),(.562,1.164)]
            self.relieve("Lente estriada de faro",reflejar(lente),1,"faro",.021,.018)
            for i,y in enumerate(muestras(.561,.795,14)):
                z = mezcla(1.126,1.110,i/14)
                self.tubo("Canal vertical del reflector",[
                    self.cara((lado*(y+.027*t*(1-i/14)),mezcla(.970,z,t)),1,.041)
                    for t in muestras(0,1,5)],.0024,"relieve_faro")
            ambar = [(.825,.954),(.924,.955),(.911,1.143),(.816,1.146)]
            self.relieve("Intermitente ámbar de esquina",reflejar(ambar),1,"ambar",.025,.012)
            self.tubo("Línea de cierre bajo óptica",[
                self.cara((lado*y,.946),1,.032) for y in muestras(.526,.909,22)],.0048,"burlete")
        self.defensa(1)

    def posterior(self):
        self.superficie("Travesaño azul posterior",[
            [self.cara((y,z),-1,-.019) for z in muestras(.74,1.435,11)]
            for y in muestras(-.905,.905,46)],"azul_carroceria")
        self.pieza_frontal("Junta del portón",0,1.100,1.481,.682,-1,"burlete",.000,.004)
        self.pieza_frontal("Portón de chapa azul",0,1.100,1.453,.659,-1,"azul_carroceria",.010,.018,.041)
        self.tubo("Vivo horizontal de portón",[
            self.cara((y,.854),-1,.027) for y in muestras(-.706,.706,34)],.0065,"azul_molduras")
        self.pieza_frontal("Alojamiento de la manilla de portón",0,1.311,.242,.115,-1,
                           "oscuro",.033,.013,.038)
        self.pieza_frontal("Manilla de portón",0,1.330,.199,.046,-1,"burlete",.047,.010,.019)
        self.emblema(1.085,-1,.036,1.04)
        self.tubo("Borde alzado superior del portón",[
            self.cara((y,1.452-.017*(abs(y)/.88)**3),-1,.014) for y in muestras(-.882,.882,32)],
            .023,"burlete","carroceria")
        for lado in (-1,1):
            y = lado*.834
            self.pieza_frontal("Base de piloto vertical",y,1.122,.194,.443,-1,"burlete",.003,.010)
            for z,h,mat in ((1.289,.098,"ambar"),(1.155,.168,"rojo"),(1.016,.088,"faro")):
                self.pieza_frontal("Lente de piloto " + mat,y,z,.164,h,-1,mat,.018,.015,.015)
            for dy in (-.052,-.031,-.010,.011,.032,.053):
                self.tubo("Estría de lente de reversa",[
                    self.cara((y+dy,z),-1,.034) for z in muestras(.985,1.046,8)],.0015,"relieve_faro")
        self.defensa(-1)

    def ruedas(self,ruta_goma):
        configurar_normal_goma(self.m["neumatico"],ruta_goma,.23)
        ancho = self.d["ancho_rueda"]/2
        flanco = [( .228,-.802),(.291,-.923),(.370,-1.0),(.400,-.989),(.420,-.944),(.439,-.854),
                  (.444,-.766),(.447,-.642),(.447,-.571),(.440,-.549),(.440,-.489),(.447,-.467),
                  (.447,-.142),(.447,-.112),(.439,-.075),(.439,.075),(.447,.112),(.447,.142),
                  (.447,.467),(.440,.489),(.440,.549),(.447,.571),(.447,.642),(.444,.766),
                  (.439,.854),(.420,.944),(.400,.989),(.370,1.0),(.291,.923),(.228,.802)]
        perfil = [(r,d*ancho) for r,d in flanco]
        llanta = [(.019,.084),(.094,.078),(.124,.104),(.166,.125),(.201,.139),(.224,.140),(.238,.129),
                  (.237,.116),(.227,.106),(.226,-.108),(.204,-.119),(.195,-.105),
                  (.186,.110),(.116,.077),(.085,.060),(.019,.060)]
        ventanas = [(a-.393,a+.393,.108,.194) for a in (math.tau*i/5+math.pi/10 for i in range(5))]
        construir_ruedas_volumetricas(self.d,self.m,self.g,perfil,llanta,segmentos_neumatico=60,
                                     segmentos_llanta=44,dibujo_banda=(.440,.123,.004),
                                     ventanas_aleacion=ventanas,desp_agujero=.103,n_tuercas=5,
                                     radio_tuercas=.064,radio_buje=.080,desp_buje=.101)
        for n,pivote in self.g.items():
            if n.startswith("rueda_"):
                x,y,z = pivote.matrix_world.translation
                lado = math.copysign(1,y)
                self.cilindro("Disco de freno",(x,y+lado*.035,z),.192,.023,"oscuro",grupo=n)
                self.cilindro("Centro azul de la llanta",(x,y+lado*.124,z),.035,.012,"azul_emblema",grupo=n)
                for pieza in pivote.children:
                    if pieza.name.startswith("Tuerca rueda"):
                        pieza.location.y += lado*.010


def main(args=None):
    if args is None:
        args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    bpy.ops.wm.read_factory_settings(use_empty=True)
    escena = bpy.context.scene
    escena.unit_settings.system = "METRIC"
    escena.view_settings.view_transform = "AgX"
    escena.view_settings.look = "AgX - Medium High Contrast"
    datos = json.loads((AQUI / (ID + ".json")).read_text())
    ford = Ford(datos)
    ford.carroceria()
    ford.cabina()
    ford.caja_cerrada()
    ford.interiores()
    ford.frontal()
    ford.posterior()
    ford.ruedas(AQUI.parents[1] / "texturas/Rubber004_1K-JPG_NormalGL.jpg")
    movimiento = preparar_rig_y_clips(datos,ford.g)
    raiz = ford.g["raiz"]
    bpy.context.view_layer.update()
    destino = SALIDA if "--publicar" in args else REVISION
    REVISION.mkdir(parents=True,exist_ok=True)
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type == "VIEW_3D":
                espacio = area.spaces.active
                espacio.region_3d.view_perspective = "CAMERA"
                espacio.shading.color_type = "MATERIAL"
                espacio.overlay.show_overlays = False
    referencia = RAIZ / "autos/generadas" / (datos["referencia"] + "_diseno_miciudad.png")
    maestro = destino / (ID + ".blend")
    configurar_estudio_y_renderizar(raiz,datos,maestro,ruta_referencia=referencia,sin_render=True)
    consolidar_lotes(raiz,("neumatico",),"llanta")
    for objeto in escena.objects:
        if objeto.type == "MESH" and objeto.parent:
            objeto.data.validate()
    ficha = validar_geometria_vehiculo(raiz,datos,destino / (ID + ".ficha.json"),{
        "movimiento": movimiento, "referencia": datos["referencia"],
        "normal_goma": {"fuente": "ambientCG Rubber004", "licencia": "CC0 1.0"},
        "clips": ["rodar_adelante","rodar_atras"],
    })
    print("FLOTA_VALIDACION",json.dumps(ficha,ensure_ascii=False),flush=True)
    exportar_glb_vehiculo(raiz,destino / (ID + ".glb"))
    if "--sin-render" in args:
        return
    bpy.ops.wm.open_mainfile(filepath=str(maestro))
    escena = bpy.context.scene
    escena.cycles.samples = 21
    bpy.data.objects["ESTUDIO_suelo_no_exportado"].scale = (8,8,8)
    resoluciones = {"perspectiva":(1100,760),"frente":(810,800),"lateral":(1300,620),
                    "trasera":(810,800),"peaton":(1100,760),"rueda":(880,790)}
    vistas = next((arg.split("=",1)[1].split(",") for arg in args if arg.startswith("--vistas=")),list(resoluciones))
    for vista in vistas:
        escena.camera = bpy.data.objects["ESTUDIO_cam_" + vista]
        escena.camera.data.clip_end = 1500
        escena.render.resolution_x, escena.render.resolution_y = resoluciones[vista]
        escena.render.filepath = str(REVISION / (vista + ".png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
