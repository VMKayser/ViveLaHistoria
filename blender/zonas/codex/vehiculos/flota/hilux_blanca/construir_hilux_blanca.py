"""Hilux de la lámina 04: doble cabina, caja independiente y defensa tubular."""
import math
from pathlib import Path
import sys

AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from carroceria_moderna import Moderno
from taller_lamina import contorno, ejecutar_modelo, intervalo, rectangulo
from kit_vehiculo_bpy import interpolar_hermite


class Hilux(Moderno):
    def frontal(self):
        toma=[(-.408,.614),(.408,.614),(.568,.718),(.552,.911),(.417,1.016),
              (-.417,1.016),(-.552,.911),(-.568,.718)]
        self.fascia(1,[(.299,.562,"pintura",None),(.562,1.043,"pintura",toma),
                       (1.043,1.107,"pintura",None)],lambda u:self.capo(self.extremos[1],u))
        self.lamas(toma,(.662,.710,.762,.81,.86,.906,.950,.981),-.026)
        self.insignia("toyota",.923,1,.026,escala=1.03)
        self.forma("Plata del protector inferior",[(-.633,.392),(-.561,.477),(-.475,.514),
                  (.475,.514),(.561,.477),(.633,.392),(.571,.368),(-.571,.368)],1,"plata",.013,.012,.021)
        self.forma("Boca de aire en faldón",[(-.453,.423),(.453,.423),(.491,.461),(.441,.485),
                  (-.441,.485),(-.491,.461)],1,"oscuro",.026,.008,.014)
        self.placa(.430,1,.049)

        for s in (-1,1):
            lado=lambda p:[(s*y,z) for y,z in p]
            self.faro("faro barrido Hilux",lado([(.421,.983),(.730,1.097),(.789,1.082),
                      (.792,.987),(.731,.918),(.472,.881)]),1,[(s*.608,.973,.042),(s*.717,1.001,.037)])
            self.vivo("Guía lumínica inferior quebrada",lado([(.463,.905),(.551,.898),(.703,.927),(.774,.985)]),
                       1,.039,.0064,"luz")
            self.forma("Inserto oscuro del antiniebla",lado([(.639,.531),(.756,.545),(.815,.768),
                      (.767,.797),(.720,.660),(.642,.606)]),1,"grafito",.017,.014,.021)
            for mat,r,prof in (("plata",.045,.038),("lente",.032,.050)):
                self.cilindro("Módulo redondo de antiniebla",self.cara((s*.707,.573),1,prof),r,.012,mat,"X")
        self.defensa_tubular()

    def defensa_tubular(self):
        for s in (-1,1):
            perfil=[(.354,.527),(.391,.549),(.533,.551),(.747,.520),
                    (.936,.451),(1.014,.412),(1.034,.396)]
            px=[(.354,2.344),(.391,2.460),(.533,2.626),(.747,2.667),
                (.936,2.620),(1.014,2.584),(1.034,2.536)]
            pts=[(interpolar_hermite(px,z),s*interpolar_hermite(perfil,z),z)
                 for z in intervalo(.354,1.034,39)]
            self.tubo("Montante curvado y volumétrico de defensa",pts,.047,"grafito")
            self.bloque("Anclaje de defensa",(2.378,s*.527,.376),(.174,.128,.083),"oscuro",.023)
        for z,x,w in ((1.018,2.582,.411),(.703,2.657,.54),(.533,2.616,.537)):
            self.tubo("Travesaño de defensa",[(x+.017*(1-(y/w)**2),y,z) for y in intervalo(-w,w,27)],
                      .032,"grafito")

    def posterior(self):
        x0,x1=self.d["caja"]
        self.fascia(-1,[(.287,.66,"grafito",None),(.66,1.265,"pintura",None)],lambda u:(
                    self.extremos[0],self.flanco(self.extremos[0],self.borde(self.extremos[0]),1)[1]*u,
                    self.borde(self.extremos[0])+.012))
        self.panel_porton(1.285,.671,1.254)
        self.insignia("toyota",1.003,-1,.027,escala=.88)
        self.forma("Manilla integrada de compuerta",
                   [(-.186,1.134),(.187,1.134),(.207,1.177),(-.194,1.177)],-1,"grafito",.014,.010,.018)
        self.sello("Luz central en manilla",0,1.155,.271,.023,-1,"rojo",.031,.006,.010)
        self.sello("Nicho de matrícula en defensa",0,.485,.642,.267,-1,"oscuro",.013,.011,.031)
        self.placa(.472,-1,.036)
        for s in (-1,1):
            lado=lambda p:[(s*y,z) for y,z in p]
            self.forma("Revestimiento de pisadera de defensa",lado([(.364,.499),(.754,.494),(.794,.539),
                      (.792,.594),(.399,.586)]),-1,"hule",.008,.013,.027)
            self.forma("Caja de piloto vertical",lado([(.663,.711),(.789,.717),(.827,.787),
                      (.826,1.128),(.777,1.239),(.667,1.227)]),-1,"rojo_oscuro",.010,.012,.023)
            for z,w,h,mat in ((1.123,.127,.161,"rojo"),(.986,.136,.086,"rojo"),
                              (.898,.131,.059,"ambar"),(.817,.115,.062,"lente")):
                self.sello("Óptica segmentada de piloto",s*.738,z,w,h,-1,mat,.028,.009,.018)
            mapa=lambda p,e:self.flanco(*p,s,e)
            self.relieve("Piloto envolvente lateral",contorno([(-2.582,.773),(-2.483,.804),
                         (-2.447,1.125),(-2.531,1.226),(-2.582,1.228)],.025),
                         mapa,"rojo",.009,.008,invertido=s==1)
        self.caja(x0,x1)

    def caja(self,a,b):
        centro=(a+b)/2
        self.bloque("Piso entablado de caja",(centro,0,.898),(b-a,1.490,.075),"grafito",.027,"interior")
        for y in intervalo(-.677,.677,15):
            self.tubo("Canal de drenaje longitudinal de caja",[(x,y,.937) for x in intervalo(a+.024,b-.025,22)],
                      .0057,"hule","interior")
        for lado in (-1,1):
            self.piel("Pared interior continua de caja",[
                [(x,lado*.724,.913),(x,lado*.735,1.020),(x,lado*.734,1.239),
                 (x,self.flanco(x,self.borde(x),lado)[1],self.borde(x))]
                for x in intervalo(a,b,31)],"pintura","interior",invertir=lado!=1)
            self.tubo("Protector superior de borde de caja",[
                      (x,lado*(self.flanco(x,self.borde(x),lado)[1]*lado-.018),self.borde(x)+.016)
                      for x in intervalo(a,b,30)],.022,"grafito")
            self.bloque("Abultamiento interior de aleta",(self.d["ejes"][0],lado*.623,.982),
                         (.781,.263,.203),"grafito",.055,"interior")
            for x in (a+.17,b-.15):
                self.tubo("Anilla interior para carga",[(x+.028*math.cos(t),lado*.745,.994+.023*math.sin(t))
                          for t in intervalo(0,math.tau,18)[:-1]],.0052,"plata","interior",True)
        for x in (a,b):
            self.piel("Tablero transversal de caja",[
                [(x,y,.913),(x,y,1.248)] for y in intervalo(-.734,.734,24)],
                "grafito","interior",invertir=x==a)
        x=-1.83
        s=1
        z=1.142
        self.relieve("Tapa de combustible rectangular",contorno(rectangulo(x,z,.235,.166),.032),
                      lambda p,e:self.flanco(*p,s,e),"grafito",.006,.009,invertido=True)
        self.tubo("Arco tubular detrás de cabina",[
            (-1.208,-.726,1.278),(-1.224,-.666,1.464),(-1.234,-.591,1.655),
            (-1.246,-.498,1.739),(-1.246,.498,1.739),(-1.234,.591,1.655),
            (-1.224,.666,1.464),(-1.208,.726,1.278)],.046,"grafito")
        for s in (-1,1):
            self.tubo("Tirante oblicuo de arco de caja",
                      [(-1.827,s*.708,1.289),(-1.759,s*.703,1.433),
                       (-1.548,s*.665,1.614),(-1.266,s*.594,1.702)],.035,"grafito")
            self.tubo("Riostra intermedia de caja",[(-1.697,s*.700,1.489),(-1.267,s*.664,1.491)],
                       .024,"grafito")
            for x in (-1.808,-1.209):
                self.bloque("Platina de anclaje de arco de caja",(x,s*.715,1.287),
                             (.111,.14,.030),"oscuro",.011,"decoracion")


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"hilux_blanca.json",Hilux,args)


if __name__=="__main__":
    main()
