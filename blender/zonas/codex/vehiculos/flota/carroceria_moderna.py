"""Taller de chapa curva para la Montero, la EcoSport y la Hilux."""
import json
import math
from pathlib import Path

import bpy

from taller_lamina import TallerLamina, contorno, entre, intervalo, interpolar, rectangulo, verificar_holgura
from kit_vehiculo_bpy import (
    configurar_normal_goma, construir_ruedas_volumetricas, crear_vacio, interpolar_hermite,
)

AQUI = Path(__file__).resolve().parent
PALETA = {
    "pintura": ("#eeeae2", .36, .10), "sombra_chapa": ("#8f8484", .65, 0),
    "hule": ("#403b41", .71, 0), "grafito": ("#38343a", .55, .08),
    "oscuro": ("#29262d", .76, 0), "tapizado": ("#4e454c", .82, 0),
    "vidrio": ("#4b414b", .25, .02, .71), "plata": ("#ada5aa", .34, .61),
    "cromo": ("#c3babb", .28, .72), "llanta": ("#9a9298", .3, .58),
    "neumatico": ("#353137", .83, 0), "lente": ("#cbd3d8", .22, .31),
    "luz": ("#e7e3d9", .26, .17), "rojo": ("#a62337", .29, .08),
    "rojo_oscuro": ("#661e2c", .38, .04), "ambar": ("#ca7234", .34, .09),
    "placa": ("#d6cbd0", .54, .05), "azul": ("#30416a", .36, .17),
}


class Moderno(TallerLamina):
    def __init__(self, datos):
        config = json.loads((AQUI / "configuracion.json").read_text())
        datos["movimiento"] = {**config["movimiento"], **datos.get("movimiento", {})}
        datos["acabados"] = {"presupuesto_triangulos": config["presupuesto_triangulos"], "textura_goma": True}
        datos["paleta"] = {**PALETA, **datos["paleta"]}
        super().__init__(datos)
        self.extremos = (datos["chapa"][0][0], datos["chapa"][-1][0])
        self.perfiles = [[(fila[0],fila[i]) for fila in datos["chapa"]] for i in (1,2)]
        self.techo_perfiles = [[(fila[0],fila[i]) for fila in datos["techo"]] for i in (1,2)]
        self.obstaculos = []
        pint = self.m["pintura"].node_tree.nodes["Principled BSDF"]
        pint.inputs["Coat Weight"].default_value = .18
        pint.inputs["Coat Roughness"].default_value = .31
        vidrio = self.m["vidrio"].node_tree.nodes["Principled BSDF"]
        vidrio.inputs["IOR"].default_value = 1.22
        vidrio.inputs["Specular IOR Level"].default_value = .14

    def ancho(self,x):
        return interpolar_hermite(self.perfiles[0],x)

    def borde(self,x):
        return interpolar_hermite(self.perfiles[1],x)

    def techo(self,x):
        return tuple(interpolar_hermite(p,x) for p in self.techo_perfiles)

    def solera(self,x):
        return interpolar_hermite(self.d["solera"],x)

    def arco(self, eje, radio, theta):
        n = 2/self.d["exponente_arco"]
        ct, st = math.cos(theta), math.sin(theta)
        return (eje+radio*math.copysign(abs(ct)**n,ct),
                self.d["radio_rueda"]+radio*math.copysign(abs(st)**n,st))

    def paso(self,x):
        z = self.solera(x)
        n = self.d["exponente_arco"]
        for eje,r in zip(self.d["ejes"],self.d["arcos"]):
            d = abs(x-eje)/r
            if d < 1:
                z = max(z,self.d["radio_rueda"] + r*(1-d**n)**(1/n))
        return z

    def flanco(self,x,z,lado,ext=0):
        q = (z-self.d["bajo"])/(self.borde(x)-self.d["bajo"])
        sección = [(0,-.102),(.11,-.058),(.265,-.028),(.52,-.031),
                   (.70,-.010),(.79,.008),(.89,-.006),(1,-.043)]
        y = self.ancho(x) + interpolar_hermite(sección,q)
        n = self.d["exponente_arco"]
        for eje,r in zip(self.d["ejes"],self.d["arcos"]):
            rr = (abs(x-eje)**n+abs(z-self.d["radio_rueda"])**n)**(1/n)
            y += self.d["ensanche_arco"]*math.exp(-((rr-r-.033)/.079)**2)
        x_final=self.extremos[1]
        puntera=max(0,min(1,(x-x_final+.36)/.36))
        x-=self.d.get("recogida_proa_m",0)*puntera**2
        return x,lado*(y+ext),z

    def segmentos_solera(self):
        x0,x1 = self.extremos
        r0,r1 = self.d["arcos"]
        t,d = self.d["ejes"]
        return ((x0,t-r0-.011),(t+r0+.011,d-r1-.011),(d+r1+.011,x1))

    def baja(self):
        x0,x1 = self.extremos
        muestras = set(intervalo(x0,x1,78))
        muestras.update(x for x,_ in self.d["solera"])
        for x,r in zip(self.d["ejes"],self.d["arcos"]):
            muestras.update(self.arco(x,r,t)[0] for t in intervalo(0,math.pi,36))
            for evento in (x-r,x+r):
                muestras.update((evento-.002,evento-.001,evento+.001,evento+.002))
        muestras = sorted(x for x in muestras if x0<=x<=x1)
        for lado in (-1,1):
            filas = [[self.flanco(x,z,lado) for z in intervalo(self.paso(x),self.borde(x),10)]
                     for x in muestras]
            chapa = self.piel("Costado abombado",filas,"pintura",invertir=lado==1)
            labio = self.piel("Canto inferior vuelto",[[f[0],(f[0][0],f[0][1]-lado*.027,f[0][2]-.009)]
                             for f in filas],"pintura",invertir=lado!=1)
            self.obstaculos.extend((chapa,labio))
            for eje,r in zip(self.d["ejes"],self.d["arcos"]):
                self.guardabarros(lado,eje,r)
            for a,b in self.segmentos_solera():
                if b-a < .035:
                    continue
                oscuro = self.d.get("zocalo_oscuro")
                cinta = [[self.flanco(x,z,lado,extra) for z,extra in (
                    (self.solera(x)+.005,.008),(self.solera(x)+.022,.024),
                    (max(self.solera(x)+.038,self.d["nivel_zocalo"]-.025),.017),
                    (max(self.solera(x)+.040,self.d["nivel_zocalo"]),.004))]
                    for x in intervalo(a,b,max(6,round((b-a)/.057)))]
                self.obstaculos.append(self.piel("Recogida inferior estampada",cinta,
                    "grafito" if oscuro else "pintura",invertir=lado==1))
            self.puertas(lado)

        for u in (-.88,.88):
            puntos = [self.capo(x,u) for x in intervalo(self.d["bordes"][-1][0]+.04,x1-.013,31)]
            self.tubo("Junta longitudinal de capó",[(x,y,z+.0018) for x,y,z in puntos],.0027,"sombra_chapa")
        self.piel("Capó curvo con hombros estampados",
                  [[self.capo(x,u) for u in intervalo(-1,1,28)]
                    for x in intervalo(self.d["bordes"][-1][0],x1,29)],"pintura")

    def guardabarros(self,lado,eje,r):
        a = []
        t = []
        for theta in intervalo(0,math.pi,55):
            x,z = self.arco(eje,r,theta)
            if z < self.solera(x)-.005:
                continue
            p = self.flanco(x,z,lado)
            boveda = [p, (x,p[1]-lado*.030,z-.008),
                      (x,lado*(.386 if eje>0 else .44),z+.071),
                      (x,lado*.365,self.d["radio_rueda"]-.089)]
            a.append(boveda)
            filas = []
            negra = self.d.get("moldura_arco")
            for dr,extr in ((0,.002),(.012,.011),(.038,.020),(.071,.014),(.090,.003)) if negra else (
                    (0,.002),(.012,.006),(.031,.009),(.051,.002)):
                xx,zz = self.arco(eje,r+dr,theta)
                filas.append(self.flanco(xx,max(self.solera(xx)+.001,zz),lado,extr))
            t.append(filas)
        self.obstaculos.append(self.piel("Bóveda cerrada de paso",a,"oscuro","interior",invertir=lado==1))
        self.obstaculos.append(self.piel("Aleta y labio del paso",t,
            "grafito" if self.d.get("moldura_arco") else "pintura",invertir=lado!=1))

    def capo(self,x,u):
        canto = self.flanco(x,self.borde(x),1)
        y = abs(canto[1])*u
        arco = self.d["capo_arco"]*(1-abs(u)**2.7)
        nervio = .016*math.exp(-((abs(u)-.6)/.16)**2)*(1-abs(u)**3)
        return interpolar(x,canto[0],abs(u)**3.3),y,self.borde(x)+arco+nervio

    def puertas(self,lado):
        for perfil in self.d["juntas"]:
            puntos = [entre(a,b,t) for a,b in zip(perfil,perfil[1:])
                      for t in intervalo(0,1,max(2,math.ceil(math.dist(a,b)/.035)))[:-1]]
            puntos.append(perfil[-1])
            self.tubo("Junta fina de puerta",[
                self.flanco(x,z,lado,.0035) for x,z in puntos if z>=self.paso(x)+.004],
                .0024,"sombra_chapa")
        for x,z in self.d["manillas"]:
            mapa = lambda p,e: self.flanco(*p,lado,e)
            self.relieve("Cazoleta de manilla",contorno(rectangulo(x,z,.184,.057),.022),mapa,
                         "sombra_chapa",.004,.005,invertido=lado==1)
            self.relieve("Tirador de puerta",contorno(rectangulo(x,z+.003,.154,.037),.016),mapa,
                         "grafito" if self.d.get("zocalo_oscuro") or self.d.get("caja") else "plata",
                         .012,.013,invertido=lado==1)

    def lado_cabina(self,x,z):
        base = self.borde(x)
        w,h = self.techo(x)
        q = max(0,min(1,(z-base)/(h-base)))
        return interpolar(self.flanco(x,base,1)[1]-.029,w,q)+.027*math.sin(math.pi*q)

    def cabina(self):
        bordes = self.d["bordes"]
        x_min,x_max = bordes[0][1],bordes[-1][1]
        for lado in (-1,1):
            mapa = lambda p,e: (p[0],lado*(self.lado_cabina(*p)+e),p[1])
            for numero,(a,b,vidrio) in enumerate(zip(bordes,bordes[1:],self.d["ventanas"])):
                z0,z1 = self.borde(a[0]),self.borde(b[0])
                exterior = contorno([(a[0],z0),(b[0],z1),(b[1],self.techo(b[1])[1]),
                                     (a[1],self.techo(a[1])[1])],0,10)
                exterior = [(x,self.borde(x) if abs(z-interpolar(z0,z1,(x-a[0])/(b[0]-a[0])))<.001 else
                             self.techo(x)[1] if abs(z-interpolar(self.techo(a[1])[1],self.techo(b[1])[1],
                                 (x-a[1])/(b[1]-a[1])))<.001 else z) for x,z in exterior]
                self.ventana("vidrio lateral "+str(numero+1),exterior,contorno(vidrio,.047,10),
                             mapa,"pintura","hule",lado==1)
            cristales=self.d["ventanas"]
            for i in self.d.get("pilares_oscuros",[]):
                antes,despues=cristales[i-1:i+1]
                a,b=antes[1],antes[2]
                c,d=despues[0],despues[-1]
                self.piel("Garnición oscura de pilar central",[
                    [mapa(entre(entre(a,b,t),entre(c,d,t),w),.0025) for w in intervalo(0,1,5)]
                    for t in intervalo(.015,.985,14)],"grafito","decoracion",invertir=lado!=1)
            self.piel("Hombro estampado bajo cristales",[
                [self.flanco(x,self.borde(x),lado),mapa((x,self.borde(x)),.001)]
                for x in intervalo(bordes[0][0],bordes[-1][0],57)],"pintura",invertir=lado==-1)
            self.espejo(lado)
        self.piel("Techo con corona y hombro",[
            [self.superficie_techo(x,u) for u in intervalo(-1,1,33)] for x in intervalo(x_min,x_max,37)],"pintura")
        self.cristal_transversal("parabrisas",bordes[-1],1)
        self.cristal_transversal("luneta",bordes[0],-1)
        if self.d.get("barras"):
            for lado in (-1,1):
                a,b=x_min+.175,x_max-.169
                self.tubo("Riel longitudinal con apoyos",[
                    (x,self.superficie_techo(x,lado*.87)[1],self.superficie_techo(x,lado*.87)[2]+.042*math.sin(math.pi*t)**.66+.013)
                    for t in intervalo(0,1,28) for x in [interpolar(a,b,t)]],.016,"grafito")
        if self.d.get("antena"):
            x=x_max-.31
            p=self.superficie_techo(x,0)
            self.bloque("Base ovalada de antena",p,(.10,.061,.025),"grafito",.011,"decoracion")
            medidas=((.019,.045),(.043,.092)) if self.d.get("caja") else ((.072,.081),(.231,.186))
            self.tubo("Antena inclinada",[p,*[(p[0]-dx,0,p[2]+dz) for dx,dz in medidas]],.0055,"hule")

    def superficie_techo(self,x,u):
        y,z = self.techo(x)
        return x,y*u,z+.030*(1-abs(u)**2.35)

    def cristal_transversal(self,nombre,borde,signo):
        x0,x1=borde
        z0=self.borde(x0)
        w0=self.lado_cabina(x0,z0)
        w1,z1=self.techo(x1)

        def mapa(p,offset):
            u,t=p
            q=1-abs(u)**2.6
            x=interpolar(x0,x1,t)+signo*q*.062*(1-t)**1.38
            z=interpolar(z0,z1,t)+q*interpolar(.020,.030,t)
            y=(interpolar(w0,w1,t)+.020*math.sin(math.pi*t))*u
            return x+signo*offset,y,z

        self.ventana(nombre,contorno(rectangulo(0,.5,2,1),0,15),
                     contorno(rectangulo(0,.501,1.77,.841),.127,15),
                     mapa,"pintura","hule",signo<0)
        if signo>0:
            p0=self.d["bordes"][-1][0]
            remate = [[mapa((u,0),0),self.capo(p0,u)] for u in intervalo(-1,1,29)]
            self.piel("Cierre de encuentro entre cristal y capó",remate,"pintura")
        elif self.d.get("aleron"):
            self.piel("Visera superior del portón",[
                [mapa((u,1),.003),mapa((u,.995),.131*(1-.10*abs(u)))]
                for u in intervalo(-.98,.98,26)],"pintura",invertir=True)
            self.tubo("Canto del alerón",[mapa((u,.995),.131*(1-.10*abs(u)))
                                        for u in intervalo(-.98,.98,28)],.009,"grafito")
            self.tubo("Tercera luz de freno",[
                mapa((u,.957),.115) for u in intervalo(-.242,.242,13)],.013,"rojo")
        if signo>0 or "caja" not in self.d:
            for u in ((-.47,.39) if signo>0 else (-.12,)):
                self.tubo("Escobilla de "+nombre,[mapa((v,.165-.057*(v-u)),.018)
                             for v in intervalo(u-.226,u+.208,16)],.0068,"hule")
                self.tubo("Brazo de limpiaparabrisas",[mapa((u-.23,.079),.018),
                          mapa((u-.16,.118),.021),mapa((u+.013,.159),.020)],.0051,"hule")

    def espejo(self,lado):
        x,z=self.d["espejo"]
        y=lado*self.lado_cabina(x,z)
        self.tubo("Pie inclinado del espejo",[(x+.051,y,z-.044),(x+.009,y+lado*.101,z-.038),
                                             (x-.016,y+lado*.124,z+.014)],.027,"grafito")
        w=.232
        pintura="grafito" if self.d.get("caja") else "pintura"
        self.bloque("Carcasa envolvente de espejo",(x-.027,y+lado*.147,z+.019),(.214,w,.127),pintura,.049,"decoracion")
        self.bloque("Bandeja de espejo",(x-.058,y+lado*.148,z-.023),(.165,w*.946,.052),"grafito",.021,"decoracion")
        self.bloque("Vidrio de espejo",(x-.131,y+lado*.148,z+.015),(.015,w*.771,.076),"lente",.006,"decoracion")
        self.tubo("Repetidor del espejo",[(x+.072,y+lado*q,z-.006) for q in intervalo(.108,.228,13)],.0041,"luz")

    def perfil(self,signo):
        return self.d["proa" if signo>0 else "cola"]

    def semicara(self,z,signo):
        x=self.extremos[1 if signo>0 else 0]
        ancho=self.ancho(x)
        perfil=self.perfil(signo)
        q=(z-perfil[0][0])/(perfil[-1][0]-perfil[0][0])
        arco=interpolar_hermite([(0,-.137),(.08,-.09),(.22,-.044),(.60,-.009),(.83,.004),(1,-.046)],q)
        apertura=self.d.get("ancho_fascia_extra_m",0) if signo>0 else 0
        return ancho+arco+apertura*(.45+.55*q)

    def cara(self,p,signo,offset=0):
        y,z=p
        a=self.d["redondeo"][0 if signo>0 else 1]
        envolvente=a*(abs(y)/self.semicara(z,signo))**3.6
        x=interpolar_hermite(self.perfil(signo),z)+signo*(offset-envolvente)
        return x,y,z

    def piel_cara(self, nombre, signo, bajo, alto, mat):
        return self.piel(nombre,[[self.cara((u*self.semicara(z,signo),z),signo)
             for z in intervalo(bajo,alto,9)] for u in intervalo(-1,1,37)],mat,invertir=signo<0)

    def fascia(self,signo,segmentos,superior):
        p=self.perfil(signo)
        for abajo,arriba,mat,hueco in segmentos:
            if hueco:
                self.entrada(signo,abajo,arriba,hueco,mat)
            else:
                o=self.piel_cara("Piel curva de defensa" if abajo<self.d["altura_defensa"][0] else
                     "Piel curva de fascia",signo,abajo,arriba,mat)
                if signo>0:
                    self.obstaculos.append(o)

        x=self.extremos[1 if signo>0 else 0]
        for lado in (-1,1):
            z0=self.solera(x)
            zc=self.borde(x)
            # La esquina enlaza el canto exterior de la fascia y el último perfil lateral.
            for abajo,arriba,mat,_ in segmentos:
                def retorno(z,t):
                    f=self.cara((lado*self.semicara(z,signo),z),signo)
                    i=1 if signo>0 else 0
                    cambio=self.d["altura_defensa"][0 if signo>0 else 1]
                    empalme=max(0,(cambio-z)/(cambio-p[0][0]))**1.4
                    aleta=self.d["ejes"][i]+signo*(self.d["arcos"][i]+.038)
                    largo=interpolar(x,aleta,.72*empalme)
                    altura=interpolar(self.solera(largo),zc,(z-p[0][0])/(p[-1][0]-p[0][0]))
                    lateral=self.flanco(largo,altura,lado,.0005)
                    pos=entre(f,lateral,t)
                    return pos[0],pos[1]+lado*.029*math.sin(math.pi*t)*empalme,pos[2]
                o=self.piel("Esquina envolvente",[[retorno(z,t) for z in intervalo(abajo,arriba,9)]
                              for t in intervalo(0,1,12)],mat,invertir=lado==signo)
                if signo>0:
                    self.obstaculos.append(o)
        self.piel("Encuentro entre fascia y panel superior",[
            [self.cara((u*self.semicara(p[-1][0],signo),p[-1][0]),signo),superior(u)]
             for u in intervalo(-1,1,37)],"pintura",invertir=signo<0)
        self.piel("Retorno inferior bajo fascia",[
            [q,(q[0]-signo*.132,q[1]*.951,q[2]-.012)]
            for u in intervalo(-1,1,38)
            for q in [self.cara((u*self.semicara(p[0][0],signo),p[0][0]),signo)]],
            "grafito",invertir=signo<0)

    def entrada(self,signo,abajo,arriba,perfil,material):
        """Piel exterior, canto interior y cavidad real de radiador."""
        h=arriba-abajo
        centro=(abajo+arriba)/2
        hueco=[(y/self.semicara(z,signo),(z-centro)/h) for y,z in perfil]
        borde=[(-1,-.5),(1,-.5),(1,.5),(-1,.5)]
        exterior,interior=emparejar_contornos(borde,hueco)

        def mapa(uv,e=0):
            u,v=uv
            z=centro+v*h
            return self.cara((u*self.semicara(z,signo),z),signo,e)

        obj=self.piel("Fascia perforada alrededor de la toma",[
            [mapa(entre(a,b,t)) for t in intervalo(0,1,5)] for a,b in zip(exterior,interior)],
            material,cerrar_u=True,invertir=signo<0)
        if signo>0:
            self.obstaculos.append(obj)
        self.piel("Canto interior de la toma",[[mapa(p,e) for e in (0,-.018,-.068)] for p in interior],
                 "grafito",cerrar_u=True,invertir=signo>0)
        self.tapa("Fondo del radiador", [mapa(p,-.072) for p in interior],"oscuro","carroceria",signo<0)

    def sello(self,nombre,y,z,w,h,signo,mat,ext=.008,corona=.010,radio=.026):
        self.forma(nombre,rectangulo(y,z,w,h),signo,mat,ext,corona,radio)

    def forma(self,nombre,perfil,signo,mat,ext=.008,corona=.010,radio=.019):
        self.relieve(nombre,contorno(perfil,radio,5),lambda p,e:self.cara(p,signo,e),mat,ext,corona,
                     invertido=signo<0)

    def vivo(self,nombre,perfil,signo,offset,radio,mat,cerrado=False):
        self.tubo(nombre,[self.cara(p,signo,offset) for p in perfil],radio,mat,cerrado=cerrado)

    def placa(self,z,signo,offset,y=0):
        self.sello("Portamatrícula",y,z,.371,.179,signo,"grafito",offset,.009,.018)
        self.sello("Matrícula",y,z,.332,.147,signo,"placa",offset+.016,.006,.014)

    def insignia(self,marca,z,signo,offset,y=0,escala=1):
        if marca=="mitsubishi":
            for giro in (0,math.tau/3,2*math.tau/3):
                perfil=[]
                for x,h in ((0,0),(-.025,.037),(0,.078),(.025,.037)):
                    perfil.append((y+escala*(x*math.cos(giro)-h*math.sin(giro)),
                                   z+escala*(h*math.cos(giro)+x*math.sin(giro))))
                self.forma("Diamante de Mitsubishi",perfil,signo,"cromo",offset,.006,.0035)
            return
        for ancho,alto,desp in ((.088,.048,0),) if marca=="ford" else (
                (.087,.052,0),(.027,.051,0),(.068,.020,.024)):
            puntos=[(y+escala*ancho*math.cos(t),z+escala*(desp+alto*math.sin(t)))
                    for t in intervalo(0,math.tau,31)[:-1]]
            if marca=="ford":
                self.forma("Centro azul de insignia",puntos,signo,"azul",offset,.004,.002)
            self.vivo("Aro de la insignia",puntos,signo,offset+.009,.0046*escala,"cromo",True)
        if marca=="ford":
            perfil=[(y+d*escala,z+h*escala) for d,h in (
                (-.050,-.006),(-.013,.017),(.010,.011),(-.020,-.019),(.022,-.011),(.056,.008))]
            self.vivo("Trazo plateado del óvalo",perfil,signo,offset+.012,.0032,"luz")

    def lamas(self,perfil,zs,ext=-.024,mat="grafito"):
        for z in zs:
            lados=[]
            for (a,az),(b,bz) in zip(perfil,perfil[1:]+perfil[:1]):
                if min(az,bz)<z<max(az,bz):
                    lados.append(interpolar(a,b,(z-az)/(bz-az)))
            if len(lados)>=2:
                ancho=min(lados)+.012,max(lados)-.012
                self.vivo("Lama de parrilla",[(y,z) for y in intervalo(*ancho,30)],1,ext,.0085,mat)

    def faro(self,nombre,perfil,signo,centros,offset=.008):
        self.forma("Burlete de "+nombre,perfil,signo,"grafito",offset,.014)
        medio=(sum(p[0] for p in perfil)/len(perfil),sum(p[1] for p in perfil)/len(perfil))
        self.forma("Lente ahumada de "+nombre,[entre(medio,p,.91) for p in perfil],signo,"lente",
                   offset+.015,.009)
        for y,z,r in centros:
            pos=self.cara((y,z),signo,offset+.025)
            self.cilindro("Aro de reflector",pos,r,.015,"plata","X",lados=21)
            pos=self.cara((y,z),signo,offset+.037)
            self.cilindro("Proyector del reflector",pos,r*.68,.009,"luz","X",lados=18)

    def panel_porton(self,w,z0,z1):
        perfil=rectangulo(0,(z0+z1)/2,w,z1-z0)
        self.vivo("Junta de portón",contorno(perfil,.081,9),-1,.008,.0037,"sombra_chapa",True)

    def interiores(self):
        a,b=self.d["bordes"][0][0],self.d["bordes"][-1][0]
        medio=(a+b)/2
        self.bloque("Piso cerrado de cabina",(medio,0,.458),(b-a,1.35,.141),"oscuro",.041,"interior")
        self.obstaculos.append(self.bloque("Cubrecárter de fondo",((b+self.extremos[1])/2,0,.371),
             (self.extremos[1]-b-.11,.738,.142),"grafito",.048,"interior"))
        self.bloque("Tablero bajo parabrisas",(b-.174,0,self.borde(b)-.068),(.468,1.435,.157),"oscuro",.059,"interior")
        asiento_del=b-.848
        asiento_tras=max(a+.593,asiento_del-.982)
        for lado in (-1,1):
            y=lado*.35
            for x in (asiento_del,asiento_tras):
                self.bloque("Cojín tapizado",(x,y,.693),(.463,.476,.179),"tapizado",.074,"interior")
                respaldo=self.bloque("Respaldo tapizado",(x-.185,y,.887),(.164,.438,.418),"tapizado",.071,"interior")
                respaldo.rotation_euler.y=-.174
                self.bloque("Apoyacabezas",(x-.211,y,1.157),(.139,.216,.148),"tapizado",.052,"interior")
            for x in (asiento_del,asiento_tras):
                self.bloque("Revestimiento interior de puerta",(x,lado*.698,.865),(.678,.116,.396),"hule",.042,"interior")
        self.bloque("Consola central",(asiento_del+.163,0,.749),(.684,.183,.182),"grafito",.062,"interior")
        self.tubo("Volante de cabina",[(b-.438+.071*math.sin(t),.351+.154*math.cos(t),1.133+.142*math.sin(t))
                  for t in intervalo(0,math.tau,36)[:-1]],.014,"grafito","interior",True)
        self.bloque("Centro del volante",(b-.418,.351,1.128),(.077,.202,.086),"hule",.030,"interior")
        self.bloque("Retrovisor interior",(b-.394,0,self.techo(self.d["bordes"][-1][1])[1]-.164),
                     (.053,.246,.069),"grafito",.022,"interior")
        for x in self.d["ejes"]:
            self.cilindro("Eje inferior",(x,0,self.d["radio_rueda"]),.049,1.224,"oscuro",grupo="interior")
        if "caja" not in self.d:
            inicio=self.extremos[0]+.079
            fin=max(inicio+.37,a+.56)
            self.bloque("Fondo de maletero",((inicio+fin)/2,0,.683),(fin-inicio,1.281,.132),
                       "tapizado",.042,"interior")

    def estribos(self):
        if not self.d.get("estribos"):
            return
        (a,b)=self.segmentos_solera()[1]
        a+=.055
        b-=.064
        for lado in (-1,1):
            y=lado*(self.d["ancho"]/2-.022)
            skirt=[(x,y,.441+.049*(abs(2*t-1)**3)) for t in intervalo(0,1,27) for x in [interpolar(a,b,t)]]
            self.tubo("Estribo tubular que sigue el zócalo",skirt,.041,
                      "plata" if self.d["estribos"]=="satinado" else "grafito")
            self.bloque("Banda de pisada",((a+b)/2,y,.472),(b-a-.107,.102,.025),"grafito",.011,"decoracion")
            for desplazamiento in (-.031,0,.031):
                self.tubo("Canal antideslizante del estribo",
                          [(x,y+desplazamiento,.488) for x in intervalo(a+.086,b-.086,22)],.0035,"hule")

    def ruedas(self):
        configurar_normal_goma(self.m["neumatico"],AQUI.parent/"texturas/Rubber004_1K-JPG_NormalGL.jpg",.21)
        r,w,ra=self.d["radio_rueda"],self.d["ancho_rueda"]/2,self.d["radio_aro"]
        perfil=[(ra*.945,-.82),(r*.73,-.956),(r*.825,-1),(r*.917,-.938),(r*.976,-.816),
                (r,-.66),(r,-.56),(r-.005,-.51),(r-.005,-.43),(r,-.381),(r,-.135),
                (r-.0045,-.102),(r-.0045,.102),(r,.135),(r,.381),(r-.005,.43),
                (r-.005,.51),(r,.56),(r,.66),(r*.976,.816),(r*.917,.938),(r*.825,1),
                (r*.73,.956),(ra*.945,.82)]
        plato=[(.012,.070),(.058,.070),(.091,.058),(ra*.62,.064),(ra*.83,w*.79),
               (ra*.925,w*.91),(ra*.982,w*.94),(ra,w*.86),(ra*.975,-w*.83),
               (ra*.90,-w*.87),(ra*.88,-.036),(ra*.67,.022),(ra*.41,.039),(.012,.050)]
        tipo=self.d["tipo_aro"]
        n=self.d["radios_aro"]
        ventanas=[]
        for i in range(n):
            a=(i+.29)*math.tau/n
            semiarco=(.63 if tipo=="ancho" else (.54 if tipo=="pareado" and i%2 else .69))*math.pi/n
            ventanas.append((a-semiarco,a+semiarco,ra*(.44 if tipo=="ancho" else .40),ra*.905))
        construir_ruedas_volumetricas(self.d,self.m,self.g,[(ri,t*w) for ri,t in perfil],plato,
                segmentos_neumatico=48,segmentos_llanta=43,dibujo_banda=(r-.002,.70*w,.0032),
                ventanas_aleacion=ventanas,desp_agujero=.077,desp_buje=.072,
                n_tuercas=self.d["tuercas"],radio_tuercas=.049,radio_buje=.065)
        if self.d.get("repuesto"):
            self.repuesto()

    def repuesto(self):
        referencia=self.g["rueda_trasera_derecha"]
        padre=crear_vacio("repuesto_fijo",(-2.038,0,.965),self.g["raiz"])
        padre.rotation_euler.z=-math.pi/2
        inversa=referencia.matrix_world.inverted()
        for objeto in referencia.children:
            local=inversa@objeto.matrix_world
            nuevo=objeto.copy()
            nuevo.name="Repuesto "+objeto.name
            bpy.context.collection.objects.link(nuevo)
            nuevo.parent=padre
            nuevo.matrix_parent_inverse.identity()
            nuevo.matrix_basis=local
        self.bloque("Soporte del repuesto en compuerta",(-2.04,0,.965),(.116,.237,.217),"grafito",.028)

    def construir(self):
        self.baja()
        self.cabina()
        self.frontal()
        self.posterior()
        self.interiores()
        self.estribos()
        self.ruedas()
        return {"angulos_direccion_verificados": verificar_holgura(self,self.obstaculos)}


def emparejar_contornos(a,b):
    """Muestrea dos polígonos convexos con la misma distribución angular."""
    def cruz(p,q):
        return p[0]*q[1]-p[1]*q[0]

    centro=(sum(p[0] for p in b)/len(b),sum(p[1] for p in b)/len(b))
    aa=[(x-centro[0],y-centro[1]) for x,y in a]
    bb=[(x-centro[0],y-centro[1]) for x,y in b]
    angulos=sorted(set(round(math.atan2(y,x)%math.tau,8) for x,y in aa+bb) |
                   set(round(math.tau*i/103,8) for i in range(103)))

    def punto(poli,theta):
        direccion=(math.cos(theta),math.sin(theta))
        for p,q in zip(poli,poli[1:]+poli[:1]):
            vector=(q[0]-p[0],q[1]-p[1])
            denominador=cruz(direccion,vector)
            if abs(denominador)<1e-9:
                continue
            recorrido=cruz(p,vector)/denominador
            u=cruz(p,direccion)/denominador
            if recorrido>0 and -.000001<=u<=1.000001:
                return centro[0]+direccion[0]*recorrido,centro[1]+direccion[1]*recorrido
        raise ValueError("El centro de la toma queda fuera de su contorno")

    return [punto(aa,t) for t in angulos],[punto(bb,t) for t in angulos]
