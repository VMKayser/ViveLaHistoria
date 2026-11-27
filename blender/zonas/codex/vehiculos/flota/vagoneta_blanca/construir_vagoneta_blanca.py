"""Carrocería familiar compacta reconstruida desde la lámina 01."""
import math
from pathlib import Path
import sys

AQUI = Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from taller_lamina import (
    TallerLamina, ejecutar_modelo, entre, intervalo, interpolar, contorno,
    rectangulo, verificar_holgura,
)
from kit_vehiculo_bpy import (
    configurar_normal_goma, construir_ruedas_volumetricas, interpolar_hermite, suavizar_subsurf,
)

PINTURA = "blanco_marfil"
GOMA = "goma_marcos"
DEFENSA = "defensa_grafito"


class Vagoneta(TallerLamina):
    def __init__(self, datos):
        super().__init__(datos)
        self.ancho = [(x,w) for x,w,z in datos["chapa"]]
        self.cintura = [(x,z) for x,w,z in datos["chapa"]]
        self.obstaculos = []
        pintura = self.m[PINTURA].node_tree.nodes["Principled BSDF"]
        pintura.inputs["Coat Weight"].default_value = .12
        pintura.inputs["Coat Roughness"].default_value = .34
        vidrio = self.m["vidrio"].node_tree.nodes["Principled BSDF"]
        vidrio.inputs["IOR"].default_value = 1.16
        vidrio.inputs["Specular IOR Level"].default_value = .13

    def borde(self,x):
        return interpolar_hermite(self.cintura,x)

    def semiancho(self,x):
        return interpolar_hermite(self.ancho,x)

    def solera(self,x):
        bajo = self.d["bajo"]
        return interpolar_hermite([(-2.158,.648),(-1.938,.648),(-1.788,bajo),
                                  (1.806,bajo),(1.933,.685),(2.132,.685)],x)

    def paso(self,x):
        z = self.solera(x)
        for eje,radio in zip(self.d["ejes"],self.d["radios_paso"]):
            if abs(x-eje) < radio:
                z = max(z,self.d["centro_rueda_z"]+math.sqrt(radio*radio-(x-eje)**2))
        return z

    @staticmethod
    def giro_de_extremo(x,relacion=1):
        """Recoge las esquinas de la chapa hacia el interior del vehículo."""
        proa = max(0,(x-1.939)/.193)
        cola = max(0,(-x-1.948)/.210)
        return x + relacion*(.086*cola**2 - .092*proa**2)

    def flanco(self,x,z,lado,extra=0):
        cintura = self.borde(x)
        q = (z-self.d["bajo"])/(cintura-self.d["bajo"])
        seccion = [(0,-.107),(.075,-.065),(.16,-.031),(.42,-.016),
                   (.64,0),(.81,.006),(.91,-.007),(1,-.058)]
        ancho = self.semiancho(x)+interpolar_hermite(seccion,q)
        for eje,radio in zip(self.d["ejes"],self.d["radios_paso"]):
            distancia = math.hypot(x-eje,z-self.d["centro_rueda_z"])
            ancho += .022*math.exp(-((distancia-radio-.033)/.074)**2)
        return self.giro_de_extremo(x),lado*(ancho+extra),z

    def capo(self,x,u):
        q = 1-abs(u)**2.65
        h = .045*q+.018*math.exp(-((abs(u)-.63)/.21)**2)*q
        return self.giro_de_extremo(x,abs(u)**4),(self.semiancho(x)-.058)*u,self.borde(x)+h

    def carroceria(self):
        for lado in (-1,1):
            xs = set(intervalo(-2.158,2.132,72))
            xs.update(x for x in (-1.938,-1.788,1.806,1.933))
            zc = self.d["centro_rueda_z"]
            for eje,r in zip(self.d["ejes"],self.d["radios_paso"]):
                xs.update(eje+r*math.cos(t) for t in intervalo(-.17,math.pi+.17,36))
                for x in (eje-r,eje+r):
                    # En el perfil la parte baja de la aleta es vertical y
                    # la curva vuelve hacia dentro al alcanzar el estribo.
                    xs.update((x-.002,x-.001,x+.001,x+.002))
            filas = [[self.flanco(x,z,lado) for z in intervalo(self.paso(x),self.borde(x),15)]
                     for x in sorted(xs)]
            self.obstaculos.append(self.piel("Chapa larga de aletas y puertas",filas,PINTURA,invertir=lado==1))
            self.obstaculos.append(self.piel("Canto inferior recogido",[
                [p,(p[0],p[1]-lado*.027,p[2]-.008)] for p in (f[0] for f in filas)],
                PINTURA,invertir=lado!=1))

            for final,signo in ((filas[0],-1),(filas[-1],1)):
                self.piel("Retorno hacia la fascia" if signo>0 else "Retorno hacia el portón",[
                    [p,self.cara((p[1]-lado*.028,p[2]),signo,-.013)] for p in final],
                    PINTURA,invertir=lado==signo)
            for eje,r in zip(self.d["ejes"],self.d["radios_paso"]):
                boveda = []
                labios = []
                for t in intervalo(-.16,math.pi+.16,49):
                    x,z = eje+r*math.cos(t),zc+r*math.sin(t)
                    if z >= self.solera(x)-.006:
                        p = self.flanco(x,z,lado)
                        labios.append([p,(x,p[1]-lado*.014,z+.010),(x,p[1]-lado*.029,z-.007)])
                        ancho = .416 if eje>0 else .480
                        boveda.append([(x,p[1]-lado*.021,z+.006),
                                       (x,lado*ancho,z+.075),(x,lado*(ancho-.018),zc-.062)])
                self.obstaculos.extend((
                    self.piel("Labio interior del paso",labios,"pintura_sombra",invertir=lado!=1),
                    self.piel("Bóveda cerrada de rueda",boveda,"oscuro","interior",invertir=lado==1),
                ))
            self.puertas(lado)

        self.piel("Capó descendente con hombro abombado",[
            [self.capo(x,u) for u in intervalo(-1,1,32)]
            for x in intervalo(.990,2.132,35)],PINTURA)
        for lado in (-1,1):
            puntos = [self.capo(x,lado*.898) for x in intervalo(1.033,2.128,31)]
            self.tubo("Junta fina del capó",[(x,y,z+.0015) for x,y,z in puntos],.0025,"pintura_sombra")
            x,y,z = self.capo(1.153,lado*.543)
            self.bloque("Surtidor de lavaparabrisas",(x,y,z+.003),(.023,.018,.009),GOMA,.006,"decoracion")

    def puertas(self,lado):
        perfiles = [
            [(-1.091,1.052),(-1.099,.860),(-1.083,.777),(-.989,.738),(-.888,.647),(-.785,.459),
             (-.737,.340),(-.669,.319),(-.168,.320),(-.152,.488),(-.157,1.036)],
            [(-.145,1.033),(-.144,.512),(-.156,.318),(.904,.317),(.973,.360),(1.002,.585),(1.011,1.026)]
        ]
        for perfil in perfiles:
            # Se conserva el paso recortado de la aleta al bajar la junta trasera.
            muestras = []
            for a,b in zip(perfil,perfil[1:]):
                for t in intervalo(0,1,max(2,round(math.dist(a,b)/.026)))[:-1]:
                    x,z = entre(a,b,t)
                    if z >= self.paso(x)+.007:
                        muestras.append(self.flanco(x,z,lado,.0039))
            self.tubo("Junta de puerta lateral",muestras,.0027,"pintura_sombra")
        for a,b in ((-.892,-.171),(-.133,1.167)):
            self.piel("Moldura lateral estampada",[
                [self.flanco(x,z,lado,min(1,(x-a)*28,(b-x)*28)*offset) for z,offset in
                 ((.596,.002),(.608,.008),(.633,.010),(.649,.003))]
                for x in intervalo(a,b,26) if self.paso(x)<.593],PINTURA,invertir=lado==1)
            self.tubo("Sombra inferior de moldura",[
                self.flanco(x,.605,lado,.004) for x in intervalo(a+.020,b-.020,23) if self.paso(x)<.590],
                .0027,"pintura_sombra")
        for x in (-.940,.053):
            y = self.flanco(x,.937,lado)[1]
            self.bloque("Encastre ovalado de manilla",(x,y,.934),(.184,.035,.077),GOMA,.026,"decoracion")
            self.bloque("Tirador en cazoleta",(x,y+lado*.020,.939),(.149,.013,.042),DEFENSA,.021,"decoracion")
        self.cilindro("Cerradura de conductor",(.093,self.flanco(.093,.891,lado,.006)[1],.891),
                      .008,.007,"cromo")

    def lado_cabina(self,x,z):
        d = self.d["cabina"]
        base = self.borde(x)
        t = max(0,min(1,(z-base)/(d["altura_lateral_techo"]-base)))
        return interpolar(self.semiancho(x)-.077,d["semiancho_lateral_techo"],t)+.033*math.sin(math.pi*t)

    def cabina(self):
        d = self.d["cabina"]
        h,w = d["altura_lateral_techo"],d["semiancho_lateral_techo"]
        bordes = d["bordes"]
        for lado in (-1,1):
            def mapa(p,ext):
                x,z = p
                return self.giro_de_extremo(x),lado*(self.lado_cabina(x,z)+ext),z
            for i, (a,b,vidrio) in enumerate(zip(bordes,bordes[1:],d["ventanas"])):
                z0,z1 = self.borde(a[0]),self.borde(b[0])
                marco = [(a[0],z0),(b[0],z1),(b[1],h),(a[1],h)]
                exterior = contorno(marco,0,12)
                exterior = [(x,self.borde(x) if abs(z-interpolar(z0,z1,(x-a[0])/(b[0]-a[0])))<.001 else z)
                            for x,z in exterior]
                self.ventana(("paño fijo lateral","ventana de puerta trasera","ventana de puerta delantera")[i],
                             exterior,contorno(vidrio,.056,12),mapa,PINTURA,GOMA,lado==1)
            self.tubo("Separador posterior de guía",[
                mapa((interpolar(-.748,-.825,t),interpolar(1.111,1.54,t)),.001)
                for t in intervalo(0,1,15)],.010,GOMA)
            self.piel("Hombro de cintura bajo ventanas",[
                [self.flanco(x,self.borde(x),lado),mapa((x,self.borde(x)),.0015)]
                for x in intervalo(bordes[0][0],.991,67)],PINTURA,invertir=lado==-1)
            self.espejo(lado)

        a,b = bordes[0][1],bordes[-1][1]
        self.piel("Techo largo con hombros curvos",[
            [(interpolar(a,b,t)+(1-u*u)*(.035 if t==0 else -.034 if t==1 else 0),
              w*u,h+(1-abs(u)**2.5)*(.042+.011*math.sin(math.pi*t)))
             for u in intervalo(-1,1,36)] for t in intervalo(0,1,30)],PINTURA)
        self.cristal_transversal("parabrisas",bordes[-1],1)
        self.cristal_transversal("luneta del portón",bordes[0],-1)

    def cristal_transversal(self,nombre,borde,signo):
        x0,x1 = borde
        d = self.d["cabina"]
        z0,z1 = self.borde(x0),d["altura_lateral_techo"]
        w0,w1 = self.lado_cabina(x0,z0),d["semiancho_lateral_techo"]

        def mapa(p,ext=0):
            u,t = p
            arco = 1-abs(u)**2.5
            ajuste = interpolar(.052*signo,-.034 if signo>0 else .035,t)
            y = u*(interpolar(w0,w1,t)+.025*math.sin(math.pi*t))
            x = self.giro_de_extremo(interpolar(x0,x1,t)+arco*ajuste,abs(u)**4)
            return (x+signo*ext,y,
                    interpolar(z0,z1,t)+arco*interpolar(.021,.042,t))

        self.ventana(nombre,contorno(rectangulo(0,.5,2,1),0,17),
                     contorno(rectangulo(0,.502,1.795,.843),.112,17),
                     mapa,PINTURA,GOMA,signo<0)
        if signo<0:
            self.piel("Pestaña blanca bajo la luneta",[
                [mapa((u,0)),self.cara((u*.739,1.049),-1,-.010)]
                for u in intervalo(-1,1,37)],PINTURA,invertir=True)
        escobillas = (-.56,.39) if signo>0 else (-.26,)
        for u in escobillas:
            self.tubo("Brazo del limpiaparabrisas",[mapa((u-.21,.084),.015),
                      mapa((u-.145,.142),.020),mapa((u+.071,.167),.018)],.0062,GOMA)
            self.tubo("Escobilla de " + nombre,[
                mapa((v,.169-.075*(v-u)),.018) for v in intervalo(u-.173,u+.282,17)],.0088,"oscuro")

    def espejo(self,lado):
        x,z = .731,1.185
        y = lado*self.lado_cabina(x,z)
        self.tubo("Pie de retrovisor",[(x+.032,y,1.146),(x+.003,y+lado*.083,1.139),
                    (x-.018,y+lado*.117,1.179)],.028,DEFENSA)
        pieza = self.bloque("Carcasa de retrovisor",(x-.032,y+lado*.138,z),
                           (.166,.221,.106),DEFENSA,.038,"decoracion")
        suavizar_subsurf(pieza,1)
        self.bloque("Cristal de retrovisor",(x-.116,y+lado*.138,z),
                    (.012,.163,.070),"relieve_faro",.005,"decoracion")

    @staticmethod
    def cara(p,signo,ext=0):
        y,z = p
        if signo>0:
            perfil = [(.237,2.105),(.298,2.175),(.417,2.201),(.584,2.216),
                      (.676,2.191),(.751,2.151),(.814,2.113),(.854,2.097)]
            caida = .118*(abs(y)/.812)**4
        else:
            perfil = [(.223,-2.043),(.270,-2.128),(.412,-2.193),(.566,-2.213),
                      (.647,-2.190),(.787,-2.172),(1.033,-2.158),(1.09,-2.127)]
            caida = .099*(abs(y)/.803)**4
        x = interpolar_hermite(perfil,z) + signo*(ext-caida)
        return x,y,z

    def sello(self,nombre,y,z,w,h,signo,mat,ext,corona=.009,radio=.028):
        mapa = lambda p,s: self.cara(p,signo,s)
        self.relieve(nombre,contorno(rectangulo(y,z,w,h),radio,5),mapa,mat,ext,corona,
                     invertido=signo<0)

    def toma(self,nombre,base,alto,ancho,z0,z1,semiancho):
        exterior = contorno(rectangulo(0,(base+alto)/2,2*semiancho,alto-base),0,16)
        interior = contorno(rectangulo(0,(z0+z1)/2,ancho,z1-z0),.037,16)
        self.obstaculos.append(self.piel(nombre,[
            [self.cara(entre(p,q,t),1) for t in intervalo(0,1,6)] for p,q in zip(exterior,interior)],
            DEFENSA,cerrar_u=True))
        retorno = [[self.cara(p,1,e) for e in (0,-.018,-.050)] for p in interior]
        self.piel("Canto de entrada inferior",retorno,DEFENSA,cerrar_u=True,invertir=True)
        self.tapa("Fondo abierto al radiador",[f[-1] for f in retorno],"oscuro","carroceria")
        for y in intervalo(-ancho*.38,ancho*.38,6):
            self.tubo("Divisor vertical de entrada",[
                self.cara((y,z),1,-.031) for z in intervalo(z0+.007,z1-.006,7)],.0046,GOMA)

    def defensas(self):
        self.toma("Travesaño de grafito con entrada inferior",.249,.467,1.100,.305,.425,.808)
        self.toma("Travesaño de grafito con entrada superior",.467,.644,1.227,.502,.571,.808)

        def frente(p):
            y,t = p
            z = interpolar(.249,.644,t)
            return self.cara((y,z),1)

        def trasera(p):
            y,t = p
            z = interpolar(.234,.647,t)+.019*(abs(y)/.803)**3
            return self.cara((y,z),-1)

        self.obstaculos.append(self.piel("Defensa trasera de cuerpo envolvente",[
            [trasera((y,t)) for t in intervalo(0,1,14)] for y in intervalo(-.803,.803,54)],
            DEFENSA,invertir=True))
        for lado in (-1,1):
            for signo,mapa,w in ((1,frente,.808),(-1,trasera,.803)):
                def retorno(t,u):
                    inicio = mapa((lado*w,t))
                    if signo>0:
                        x,z = interpolar(1.884,1.824,t),interpolar(.258,.672,t)
                    else:
                        x,z = interpolar(-1.804,-1.928,t),interpolar(.252,.650,t)
                    y = self.flanco(x,z,lado,.017)[1]
                    intermedio = entre(inicio,(x,y,z),u)
                    return (intermedio[0],intermedio[1]+lado*.024*math.sin(math.pi*u),intermedio[2])
                filas = [[retorno(t,u) for t in intervalo(0,1,18)] for u in intervalo(0,1,22)]
                self.obstaculos.append(self.piel("Puntera lateral de defensa",filas,DEFENSA,
                                               invertir=lado==signo))
                self.obstaculos.append(self.piel("Pestaña superior de defensa",[
                    [f[-1],(f[-1][0],f[-1][1]-lado*.034,f[-1][2]+.013)] for f in filas],
                    DEFENSA,invertir=lado!=signo))
                self.obstaculos.append(self.piel("Canto de defensa vuelto al interior",[
                    [p,(p[0]+signo*.014,p[1]-lado*.035,p[2]+.003)] for p in filas[-1]],DEFENSA,
                    invertir=lado!=signo))
            self.sello("Intermitente rectangular en defensa",lado*.682,.543,.220,.069,1,GOMA,.009,.009,.016)
            self.sello("Lente ámbar de defensa",lado*.683,.543,.187,.050,1,"ambar",.023,.008,.013)

    def insignia(self,z,signo,offset,escala):
        mapa = lambda y,h: self.cara((y,z+h),signo,offset)
        puntos = [mapa(.046*escala*math.cos(t),.031*escala*math.sin(t))
                  for t in intervalo(0,math.tau,32)[:-1]]
        self.tubo("Óvalo metálico de insignia",puntos,.0048*escala,"cromo",cerrado=True)
        self.tubo("Barra central de insignia",[mapa(y,0) for y in
                  intervalo(-.053*escala,.053*escala,9)],.005*escala,"cromo")

    def frontal(self):
        self.piel("Frente continuo bajo borde del capó",[
            [self.capo(2.132,u),self.cara((u*.694,.793),1,-.021),
             self.cara((u*.738,.675),1,-.016),self.cara((u*.789,.632),1,-.012)]
            for u in intervalo(-1,1,32)],PINTURA,invertir=True)
        self.sello("Hueco de parrilla superior",0,.727,.811,.140,1,GOMA,.001,.006,.027)
        self.sello("Fondo oscuro de parrilla de lamas",0,.728,.779,.112,1,"oscuro",.010,.006,.020)
        for z in (.691,.723,.757):
            self.tubo("Lama de parrilla",[
                self.cara((y,z),1,.022) for y in intervalo(-.390,.390,20)],.0056,DEFENSA)
        self.insignia(.727,1,.035,.76)

        for lado in (-1,1):
            def forma(poligono):
                return contorno([(y*lado,z) for y,z in poligono],.029,7)

            mapa = lambda p,s: self.cara(p,1,s)
            borde = [(.369,.660),(.773,.655),(.792,.765),(.423,.809)]
            self.relieve("Junta envolvente de faro",forma(borde),mapa,GOMA,.009,.008)
            faro = [(.389,.669),(.693,.666),(.720,.765),(.434,.794)]
            self.relieve("Lente doble ligeramente abombada",forma(faro),mapa,"lente_clara",.024,.011)
            self.sello("Reflector principal",lado*.517,.731,.174,.079,1,"relieve_faro",.033,.010,.021)
            self.sello("Reflector exterior",lado*.648,.725,.080,.077,1,"lente_clara",.037,.008,.018)
            for y in (.444,.478,.514,.548,.583,.62,.652,.679):
                self.tubo("Flutes de óptica clara",[
                    self.cara((lado*y,z),1,.047) for z in intervalo(.682,.759,9)],.0016,"lente_clara")
            ambar = [(.704,.668),(.767,.665),(.778,.752),(.723,.770)]
            self.relieve("Intermitente angular en óptica",forma(ambar),mapa,"ambar",.018,.012)
            self.tubo("Filo bajo óptica",[
                self.cara((lado*y,.657),1,.022) for y in intervalo(.403,.770,18)],.0032,GOMA)
        self.placa(0,.370,1,.020)

    def posterior(self):
        self.piel("Silueta baja del portón inclinado",[
            [self.cara((y,z),-1,-.011) for z in intervalo(.622,1.053,15)]
            for y in intervalo(-.739,.739,43)],PINTURA,invertir=True)
        self.sello("Burlete del portón de vagoneta",0,.816,1.356,.432,-1,"pintura_sombra",.004,.004,.058)
        perfil = rectangulo(0,.822,1.328,.420)
        self.relieve("Chapa abombada del portón",contorno(perfil,.067,14),
                     lambda p,e:self.cara(p,-1,e),PINTURA,.009,.013,invertido=True)
        self.sello("Borde de prensa del alojamiento de matrícula",0,.820,.678,.268,-1,"pintura_sombra",.024,.009,.052)
        self.sello("Paño cóncavo del alojamiento",0,.812,.631,.224,-1,PINTURA,.026,.014,.056)
        self.sello("Manija superior de portón",0,.921,.257,.029,-1,GOMA,.037,.007,.012)
        self.placa(0,.803,-1,.045)
        self.insignia(1.006,-1,.033,.87)
        for lado in (-1,1):
            y = lado*.734
            self.sello("Caja vertical de piloto",y,.825,.139,.347,-1,GOMA,.029,.007)
            for z,h,mat in ((.958,.088,"ambar"),(.847,.122,"rojo"),(.746,.068,"lente_clara")):
                self.sello("Lente apilada de piloto " + mat,y,z,.122,h,-1,mat,.039,.010,.017)
            for dy in (-.037,-.012,.013,.039):
                self.tubo("Estrías de reversa trasera",[
                    self.cara((y+dy,z),-1,.052) for z in intervalo(.725,.766,7)],.0015,"relieve_faro")

    def placa(self,y,z,signo,ext):
        self.sello("Marco de matrícula",y,z,.332,.172,signo,GOMA,ext,.008,.018)
        self.sello("Matrícula lisa",y,z,.303,.143,signo,"matricula",ext+.013,.006,.013)
        for dy in (-.121,.121):
            self.cilindro("Remache de matrícula",self.cara((y+dy,z+.045),signo,ext+.021),.0037,.006,"cromo","X")

    def interior(self):
        self.bloque("Piso de habitáculo",(-.195,0,.364),(2.62,1.42,.147),"oscuro",.042,"interior")
        self.bloque("Piso del maletero",(-1.581,0,.565),(1.101,1.327,.089),"tapizado",.033,"interior")
        self.bloque("Revestimiento interior del portón",(-2.091,0,.794),(.105,1.320,.421),
                    GOMA,.044,"interior")
        self.bloque("Tablero compacto",(.877,0,.996),(.436,1.405,.171),"oscuro",.064,"interior")
        self.bloque("Visera del cuadro",(.795,.341,1.089),(.206,.391,.064),GOMA,.029,"interior")
        self.bloque("Consola baja",(.345,0,.637),(.474,.188,.158),GOMA,.047,"interior")
        self.bloque("Banqueta de pasajeros",(-.636,0,.632),(.538,1.215,.208),"tapizado",.073,"interior")
        respaldo = self.bloque("Respaldo de banqueta",(-.879,0,.849),(.147,1.238,.396),
                               "tapizado",.069,"interior")
        respaldo.rotation_euler.y = -.149
        for lado in (-1,1):
            y = lado*.339
            for x,z,alto in ((.079,1.152,.167),(-.897,1.101,.123)):
                self.bloque("Apoyacabezas tapizado",(x,y,z),(.132,.243,alto),
                            "tapizado",.046,"interior")
            self.bloque("Cojín de asiento delantero",(.249,y,.659),(.461,.437,.171),
                        "tapizado",.074,"interior")
            respaldo = self.bloque("Respaldo delantero",(.035,y,.861),(.156,.408,.418),
                                   "tapizado",.068,"interior")
            respaldo.rotation_euler.y = -.163
            for x in (-.539,.411):
                self.bloque("Revestimiento de puerta",(x,lado*.684,.825),(.704,.121,.331),
                            "tapizado",.050,"interior")
            self.bloque("Panel de maletero sobre la rueda",(-1.243,lado*.595,.691),(.631,.214,.251),
                        GOMA,.072,"interior")
        self.tubo("Aro de volante",[(.612+.056*math.sin(t),.348+.147*math.cos(t),1.026+.143*math.sin(t))
                                  for t in intervalo(0,math.tau,37)[:-1]],.014,"oscuro","interior",True)
        self.bloque("Cubierta central de volante",(.616,.348,1.027),(.063,.206,.078),
                    GOMA,.027,"interior")
        self.tubo("Columna de dirección",[(.614,.348,1.024),(.837,.348,.912)],.026,"oscuro","interior")
        self.bloque("Espejo del salón",(.395,0,1.456),(.053,.251,.071),
                    GOMA,.024,"interior")
        self.tubo("Pie de espejo interior",[(.397,0,1.459),(.451,0,1.507)],.014,GOMA,"interior")
        self.bloque("Larguero inferior",(-.030,0,.291),(4.09,.714,.164),"oscuro",.047,"interior")
        self.obstaculos.append(self.bloque("Cubrecárter", (1.55,0,.357),(1.13,.736,.147),
                               "oscuro",.047,"interior"))
        for x in self.d["ejes"]:
            self.cilindro("Travesaño de eje", (x,0,self.d["centro_rueda_z"]),.044,1.250,"oscuro",
                          grupo="interior")
        self.cilindro("Salida de escape",(-2.036,-.462,.265),.036,.166,"oscuro","X","interior")
        self.cilindro("Boquilla de escape",(-2.111,-.462,.265),.034,.009,GOMA,"X","interior")

    def ruedas(self):
        goma = AQUI.parents[1] / "texturas/Rubber004_1K-JPG_NormalGL.jpg"
        configurar_normal_goma(self.m["neumatico"],goma,.21)
        a = self.d["ancho_rueda"]/2
        perfil = [(.180,-.73),(.239,-.93),(.277,-1),(.299,-.96),(.316,-.87),
                  (.324,-.76),(.328,-.65),(.328,-.60),(.323,-.56),(.323,-.46),(.328,-.42),
                  (.328,-.11),(.323,-.086),(.323,.086),(.328,.11),
                  (.328,.42),(.323,.46),(.323,.56),(.328,.60),(.328,.65),
                  (.324,.76),(.316,.87),(.299,.96),(.277,1),(.239,.93),(.180,.73)]
        neumatico = [(r,d*a) for r,d in perfil]
        aro = [(.016,.065),(.057,.065),(.081,.048),(.122,.057),(.157,.073),
               (.170,.088),(.181,.095),(.192,.092),(.195,.077),(.188,.063),
               (.183,-.064),(.170,-.083),(.159,-.069),(.151,.051),(.101,.039),(.016,.044)]
        # Ocho bocas redondeadas cortadas de verdad en el plato de acero.
        construir_ruedas_volumetricas(self.d,self.m,self.g,neumatico,aro,segmentos_neumatico=60,
                                     segmentos_llanta=50,dibujo_banda=(.324,.074,.0034),
                                     n_ventilaciones=8,radio_ventilaciones=.141,radio_agujero=.0142,
                                     desp_agujero=.061,n_tuercas=4,radio_tuercas=.045,
                                     radio_buje=.058,desp_buje=.065)
        for nombre,pivote in self.g.items():
            if nombre.startswith("rueda_"):
                x,y,z = pivote.matrix_world.translation
                lado = math.copysign(1,y)
                self.cilindro("Disco interior", (x,y+lado*.021,z),.158,.014,"oscuro",grupo=nombre)
                for obj in pivote.children:
                    if obj.name.startswith("Tuerca rueda"):
                        obj.location.y += lado*.009

    def construir(self):
        self.carroceria()
        self.cabina()
        self.frontal()
        self.posterior()
        self.defensas()
        self.interior()
        self.ruedas()
        angulos = verificar_holgura(self,self.obstaculos)
        return {"angulos_direccion_verificados": angulos}


def main(args=None):
    if args is None:
        args = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI / "vagoneta_blanca.json", Vagoneta, args)


if __name__ == "__main__":
    main()
