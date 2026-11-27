"""EcoSport de la lámina 03: nariz compacta y rueda exterior de portón."""
from pathlib import Path
import sys

AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from carroceria_moderna import Moderno
from taller_lamina import contorno, ejecutar_modelo, intervalo


class EcoSport(Moderno):
    def frontal(self):
        parrilla=[(-.471,.506),(.471,.506),(.549,.562),(.581,.669),(.551,.730),
                  (.429,.798),(-.429,.798),(-.551,.730),(-.581,.669),(-.549,.562)]
        self.fascia(1,[(.236,.447,"grafito",None),(.447,.823,"pintura",parrilla),(.823,.984,"pintura",None)],
                    lambda u:self.capo(self.extremos[1],u))
        self.vivo("Filete satinado de parrilla trapezoidal",contorno(parrilla,.038,9),1,.005,.0085,"plata",True)
        self.lamas(parrilla,(.530,.576,.619,.666,.709,.752,.780),-.021)
        self.forma("Ranura superior entre ópticas",[(-.495,.888),(.495,.888),(.508,.925),(-.508,.925)],
                   1,"grafito",.005,.012,.014)
        self.vivo("Lama superior satinada",[(y,.907) for y in intervalo(-.487,.487,24)],1,.021,.0035,"plata")
        self.insignia("ford",.906,1,.022,escala=.80)
        self.forma("Remate frontal de defensa en plata",[(-.562,.315),(-.601,.432),(-.532,.442),(-.448,.387),
                  (.448,.387),(.532,.442),(.601,.432),(.562,.315),(.467,.289),(-.467,.289)],
                  1,"plata",.016,.015,.018)
        self.forma("Canal central bajo parrilla",[(-.411,.383),(.411,.383),(.452,.419),(.442,.447),
                  (-.442,.447),(-.452,.419)],1,"oscuro",.022,.008,.020)
        self.placa(.453,1,.040)

        for s in (-1,1):
            lado=lambda p:[(s*y,z) for y,z in p]
            self.faro("farol angular EcoSport",lado([(.455,.908),(.707,.988),(.782,.963),(.790,.909),
                     (.713,.864),(.534,.832)]),1,[(s*.622,.911,.034),(s*.706,.928,.029)])
            self.vivo("Óptica inferior quebrada",lado([(.495,.884),(.55,.852),(.692,.880),(.764,.922)]),1,.035,.0048,"luz")
            self.forma("Intermitente en vértice exterior",lado([(.750,.921),(.782,.946),(.776,.975),(.741,.975)]),
                       1,"ambar",.026,.008,.009)
            self.forma("Nicho trapezoidal del antiniebla",lado([(.585,.493),(.796,.497),(.775,.641),(.644,.671)]),
                       1,"grafito",.009,.014,.024)
            y,z=s*.698,.571
            self.cilindro("Cerco de antiniebla",self.cara((y,z),1,.030),.053,.019,"plata","X")
            self.cilindro("Antiniebla circular",self.cara((y,z),1,.043),.041,.014,"lente","X")
            self.cilindro("Reflector interno de antiniebla",self.cara((y,z),1,.054),.024,.006,"luz","X")

    def posterior(self):
        x=self.d["bordes"][0][0]
        def superior(u):
            q=1-abs(u)**2.6
            return x-.062*q,u*self.lado_cabina(x,self.borde(x)),self.borde(x)+.020*q
        self.fascia(-1,[(.228,.539,"grafito",None),(.539,1.205,"pintura",None)],superior)
        self.panel_porton(1.298,.543,1.182)
        self.forma("Placa protectora plateada posterior",[(-.503,.299),(-.438,.409),(-.305,.443),
                  (.324,.443),(.439,.413),(.503,.299)],-1,"plata",.018,.014,.021)
        self.placa(.362,-1,.044)
        self.insignia("ford",.745,-1,.026,y=-.567,escala=.72)
        self.sello("Manija del portón lateral",.565,.745,.149,.040,-1,"grafito",.018,.012,.016)
        for s in (-1,1):
            lado=lambda p:[(s*y,z) for y,z in p]
            self.forma("Caja horizontal de piloto",lado([(.409,1.014),(.775,1.040),(.807,.958),
                      (.768,.904),(.510,.910)]),-1,"rojo_oscuro",.008,.011,.020)
            self.forma("Plano rojo del piloto",lado([(.437,1.008),(.761,1.031),(.789,.96),
                      (.745,.922),(.529,.924)]),-1,"rojo",.019,.010,.019)
            self.forma("Pestaña blanca de piloto",lado([(.465,1.006),(.752,1.021),(.765,.991),(.508,.974)]),
                       -1,"lente",.035,.006,.010)
            mapa=lambda p,e:self.flanco(*p,s,e)
            self.relieve("Retorno de piloto al guardabarros",contorno([(-1.985,1.035),(-1.687,.997),
                          (-1.787,.909),(-1.989,.913)],.022),mapa,"rojo",.007,.011,invertido=s==1)
            self.forma("Reflector de defensa posterior",lado([(.573,.354),(.757,.360),(.776,.439),(.548,.442)]),
                       -1,"rojo",.013,.011,.017)


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"ecosport_blanca.json",EcoSport,args)


if __name__=="__main__":
    main()
