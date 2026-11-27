"""Remolque de pasajeros con cinco vanos por lado, techo curvo y lanza."""
import math
from pathlib import Path
import sys

AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from taller_clasicos import Clasico
from taller_lamina import ejecutar_modelo, intervalo, verificar_holgura
from kit_vehiculo_bpy import crear_vacio


class Remolque(Clasico):
    def __init__(self, datos):
        datos["paleta"]={
            **datos["paleta"],"marco":("#5a4440",.63,0),"canto":("#9b7864",.62,0),
            "duela_1":("#a78370",.73,0),"duela_2":("#a17e6c",.76,0),
            "duela_3":("#ac8874",.72,0),"duela_4":("#aa8270",.69,0),
            "techo":("#aa8a78",.78,0),"madera_banco":("#8d5738",.63,0),
            "borde_banco":("#a8754b",.64,0),"piso_claro":("#8d694c",.74,0),
        }
        super().__init__(datos)

    def bajo(self,x):
        a,_,z,_,_=self.d["caja"]
        niveles=[z+.011]
        c=self.d["radio_rueda"]
        for i,eje in enumerate(self.d["ejes"]):
            radio_x,radio_z=((.560,.560) if i==0 else (.687,.605))
            cuadrado=((x-eje)/radio_x)**2
            if cuadrado<1:
                niveles.append(c+.008+radio_z*math.sqrt(1-cuadrado))
        return max(niveles)

    def duelas(self,lado):
        a,_,piso,w,alféizar=self.d["caja"]
        frente=self.d["vano_delantero"]
        xs=intervalo(a+.026,frente,54)
        grosores=(w-.032,w-.006)
        for i,(x0,x1) in enumerate(zip(xs,xs[1:])):
            m=(x0+x1)/2
            filas=[]
            for x in (x0+.0015,m,x1-.0015):
                b=self.bajo(x)
                filas.append([(x,lado*grosores[0],b-.003),(x,lado*grosores[1],b),
                              (x,lado*grosores[1],alféizar-.008),
                              (x,lado*grosores[0],alféizar-.003)])
            pieza=self.volumen("Tabla vertical con corte inferior",filas,f"duela_{1+(i*7+i//9)%4}")
            if min(abs(m-e) for e in self.d["ejes"])<.73:
                self.obstaculos.append(pieza)
        for eje in self.d["ejes"]:
            r=.543 if eje<0 else .667
            forma=[]
            for t in intervalo(.42,math.pi-.42,46):
                x=eje+r*math.cos(t)
                z=self.bajo(x)
                forma.append([(x,lado*(w-.032),z+.013),(x,lado*(w+.031),z+.010),
                              (x,lado*(w+.041),z+.035),(x,lado*(w+.015),z+.049),
                              (x,lado*w,z+.041)])
            moldura=self.piel("Guarnición forjada sobre la rueda",forma,"metal",invertir=lado==1)
            self.obstaculos.append(moldura)
        for e in (-1,1):
            x=self.d["ejes"][1 if e>0 else 0]
            tramo=(a+.012,x-.58) if e<0 else (x+.687,frente)
            if tramo[1]-tramo[0]>.039:
                self.obstaculos.append(self.banda("Tramo recto de solera de madera",
                           [(v,lado*(w-.023),piso+.013) for v in intervalo(*tramo,14)],
                           "marco",.085,.076))
        t,d=self.d["ejes"]
        self.obstaculos.append(self.banda("Solera entre pasos de rueda",[(x,lado*(w-.021),piso+.017)
                     for x in intervalo(t+.552,d-.683,31)],"marco",.086,.077))

    def vano_lateral(self,x0,x1,lado):
        a,b,_,w,z0=self.d["caja"]
        y=lado*(w-.008)
        z1=2.401
        hueco=[]
        for x in intervalo(x0+.027,x1-.028,19):
            q=(x-(x0+x1)/2)/((x1-x0)/2-.027)
            h=z1-.075-.108*(abs(q)**4.6)
            hueco.append((x,y,h))
        self.piel("Dintel arqueado de ventana abierta",[
            [p,(p[0],p[1],z1)] for p in hueco],"marco",invertir=lado==1)
        self.piel("Dovela interior de arco",[
            [p,(p[0],p[1]-lado*.061,p[2]+.016)] for p in hueco],
            "marco","interior",invertir=lado!=1)
        self.tubo("Junquillo de dintel arqueado",[(x,y+lado*.008,z-.003) for x,y,z in hueco],
                  .010,"canto")
        x=x0+(.016 if x0<a+.012 else 0)
        self.bloque("Montante de madera de vano",(x,y-.012*lado,(z0+z1)/2),
                    (.062,.092,z1-z0+.045),"marco",.012)
        self.banda("Alféizar de ventana en madera",[(x,y,z0-.020) for x in
                    intervalo(x0+.009,x1-.009,14)],"marco",.095,.056)
        self.tubo("Vivo bajo el vano",[(x,y+lado*.047,z0+.024) for x in intervalo(x0+.023,x1-.023,16)],
                  .0055,"canto")

    def costados(self):
        a,b,piso,w,z0=self.d["caja"]
        for lado in (-1,1):
            self.duelas(lado)
            for x0,x1 in self.d["tramos"]:
                self.vano_lateral(x0,x1,lado)
            y=lado*(w-.019)
            for x in (self.d["vano_delantero"],b-.035):
                nivel=piso+.061 if x>b-.09 else self.bajo(x)+.072
                self.obstaculos.append(self.bloque("Pilar de plataforma",(x,y,(nivel+2.414)/2),
                            (.071,.104,2.414-nivel),"marco",.014))
            x_inicio=self.d["vano_delantero"]+.030
            u=b-.032
            arco=[(x,y,2.295-.126*abs((2*x-x_inicio-u)/(u-x_inicio))**3.6)
                   for x in intervalo(x_inicio,u,21)]
            self.piel("Arco de acceso lateral",[[p,(p[0],p[1],2.412)] for p in arco],
                      "marco",invertir=lado==1)
            self.tubo("Vivo superior de acceso",arco,.009,"canto")
            self.banda("Cintón longitudinal superior",[(x,y,2.353) for x in intervalo(a,b,38)],
                       "marco",.096,.073)

    def frente_trasera(self):
        a,b,piso,w,z0=self.d["caja"]
        for x,es_frente in ((a+.011,False),(b-.042,True)):
            for i,(y0,y1) in enumerate(((-w+.024,-.309),(-.309,.309),(.309,w-.023))):
                if es_frente and i==1:
                    cota=2.255
                else:
                    cota=2.284
                    for j,(y,yp) in enumerate(zip(intervalo(y0,y1,8),intervalo(y0,y1,8)[1:])):
                        base=piso+.064
                        self.bloque("Duelas del testero", (x,(y+yp)/2,(base+z0)/2),
                                   (.044,yp-y-.003,z0-base),f"duela_{1+(j+2*i)%4}",.003)
                    self.bloque("Alféizar transversal del testero",(x,(y0+y1)/2,z0),
                                 (.084,y1-y0+.015,.052),"marco",.009)
                y_medio=(y0+y1)/2
                arco=[]
                for y in intervalo(y0+.018,y1-.018,21):
                    q=(y-y_medio)/((y1-y0)/2-.018)
                    arco.append((x,y,cota+.122*(1-abs(q)**4)))
                self.piel("Dintel arqueado de testero",[
                    [p,(p[0],p[1],2.422)] for p in arco],"marco",invertir=es_frente)
                self.tubo("Filete de dintel de testero",arco,.0085,"canto")
            for y in (-.309,.309,-w+.021,w-.021):
                if es_frente and abs(y)<.4:
                    z_bajo=z0
                else:
                    z_bajo=piso+.047
                self.bloque("Pilar de testero",(x,y,(z_bajo+2.416)/2),
                           (.064,.053,2.416-z_bajo),"marco",.009)
            self.bloque("Solera transversal de testero",(x,0,piso+.043),(.071,w*2,.088),
                        "marco",.010)
        for s in (-1,1):
            y=s*.308
            self.forja("Pasamanos de latón en la entrada",[(b-.004,y,piso+.038),(b+.002,y,1.320),
                      (b-.023,y,1.451),(b-.128,y,1.459)],.021,"laton")
            self.bola("Remate de pasamanos",(b-.132,y,1.459),(.032,.030,.030),"laton")
            y=s*(w-.049)
            self.forja("Barandilla de plataforma",[(b-.042,y,1.472),(b-.281,y,1.479),
                         (b-.494,y,1.476)],.021,"laton")
            for x in (b-.067,b-.274,b-.471):
                self.cilindro("Barrote de protección de plataforma",(x,y,1.144),.013,.630,"laton_oscuro","Z")
        self.bloque("Tabla de entrada al pasillo",(b-.044,0,piso+.068),(.151,.635,.052),
                    "borde_banco",.013,"interior")
        self.bloque("Peldaño inferior exterior",(b+.084,0,piso-.073),(.236,.607,.068),"piso_claro",.014)
        for s in (-1,1):
            self.forja("Ménsula que sostiene el peldaño",[(b-.141,s*.204,piso),
                       (b-.009,s*.209,piso-.093),(b+.126,s*.222,piso-.095)],.020,"metal")

    def tejado(self):
        a,b,w,z,h=self.d["alero"]
        def superficie(x,u,esp):
            arco=h*(1-abs(u)**2.2)
            caida=.020*(1-((2*x-a-b)/(b-a))**2)
            return x,u*w,z+arco+caida+esp
        self.piel("Cubierta abovedada de madera",[
            [superficie(x,u,.033) for u in intervalo(-1,1,35)]
            for x in intervalo(a,b,48)],"techo")
        self.piel("Revestimiento interior de techo",[
            [superficie(x,u,-.024) for u in intervalo(-1,1,26)]
            for x in intervalo(a,b,39)],"piso","interior",invertir=True)
        for u in (-1,1):
            self.piel("Canto longitudinal de alero",[
                [superficie(x,u,e) for e in (.033,.009,-.031)] for x in intervalo(a,b,42)],
                "techo",invertir=u>0)
            self.tubo("Vivo continuo bajo el alero",[
                superficie(x,u,-.016) for x in intervalo(a,b,42)],.0075,"canto")
        for x in (a,b):
            self.piel("Canto arqueado del alero",[
                [superficie(x,u,e) for e in (.033,.012,-.031)] for u in intervalo(-1,1,42)],
                "techo",invertir=x==a)
        for x in intervalo(a+.080,b-.084,15):
            self.tubo("Costilla vista de techo",[superficie(x,u,-.048) for u in intervalo(-.98,.98,18)],
                      .024,"marco","interior")
        for u in intervalo(-.937,.937,15):
            self.tubo("Junta de duela del techo interior",[
                superficie(x,u,-.026) for x in intervalo(a+.026,b-.032,10)],.0028,"metal","interior")

    def bancos_y_piso(self):
        a,b,piso,w,z0=self.d["caja"]
        for i,(y0,y1) in enumerate(zip(intervalo(-.615,.615,15),intervalo(-.615,.615,15)[1:])):
            self.bloque("Duela longitudinal de suelo",((a+b)/2,(y0+y1)/2,piso+.041),
                        (b-a-.054,y1-y0-.003,.069),"piso_claro" if i%3 else "canto",.004,"interior")
        self.obstaculos.append(self.bloque("Extensión de suelo en la plataforma",
            (2.323,0,piso+.038),(.365,1.566,.075),"piso_claro",.017,"interior"))
        for tramo in self.d["tramos"]:
            x=sum(tramo)/2-.073
            for s in (-1,1):
                y=s*.534
                for dx in (-.137,-.038,.061,.160):
                    self.bloque("Listón horizontal de asiento",(x+dx,y,1.235),
                                 (.094,.386,.045),"madera_banco",.014,"interior")
                for k,z in enumerate((1.376,1.451,1.526,1.598)):
                    pl=self.bloque("Listón de respaldo",(x-.184-.015*k,y,z),
                                 (.053,.408,.076),"madera_banco" if k!=3 else "borde_banco",.014,"interior")
                    pl.rotation_euler.y=-.081
                for zz in (.386,.669):
                    v=s*zz
                    for dx in (-.128,.136):
                        self.tubo("Pie de asiento de hierro",[(x+dx,v,piso+.066),(x+dx+.025,v,1.036),
                                (x+dx,v,1.208)],.016,"metal","interior")
                    self.tubo("Armazón del respaldo",[(x-.136,v,1.216),(x-.183,v,1.408),
                                (x-.228,v,1.617)],.013,"metal","interior")
                self.tubo("Moldura delantera del banco",[(x+.200,y+d,1.236) for d in intervalo(-.179,.179,14)],
                          .009,"borde_banco","interior")

    def lanza(self):
        pivote=self.g["tornamesa_delantera"]
        grupo="tornamesa_delantera"
        eje=self.d["ejes"][1]
        radio=self.d["radio_rueda"]
        perfil=[(1.467,0,.563),(1.810,0,.580),(2.229,0,.558),(2.725,0,.516),(3.032,0,.492)]
        self.banda("Lanza de arrastre de acero",perfil,"metal",.145,.076,grupo)
        for s in (-1,1):
            self.forja("Brazo que fija la lanza al eje",[(1.526,s*.43,.602),(1.704,s*.29,.608),
                       (2.018,s*.099,.605)],.028,"metal",grupo)
        self.cilindro("Bulón transversal de lanza",(2.945,0,.527),.027,.205,"laton_oscuro",grupo=grupo)
        self.tubo("Ojo forjado de enganche",[
            (3.108+.047*math.cos(t),.061*math.cos(t),.521+.071*math.sin(t))
            for t in intervalo(0,math.tau,36)[:-1]],.0155,"acero",grupo,True)
        crear_vacio("enganche_frontal",(3.108-eje,0,.521-radio),pivote)

    def construir(self):
        self.ruedas()
        self.chasis()
        self.costados()
        self.frente_trasera()
        self.bancos_y_piso()
        self.tejado()
        self.lanza()
        return {"angulos_direccion_verificados":verificar_holgura(self,self.obstaculos)}


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"remolque_madera.json",Remolque,args)


if __name__=="__main__":
    main()
