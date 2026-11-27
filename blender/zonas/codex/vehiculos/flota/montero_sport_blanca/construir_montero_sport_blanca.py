"""Montero Sport de la lámina 02, con Dynamic Shield y doble nivel de ópticas."""
import math
from pathlib import Path
import sys

AQUI = Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from carroceria_moderna import Moderno
from taller_lamina import contorno, ejecutar_modelo, intervalo


class Montero(Moderno):
    def frontal(self):
        toma = [(-.384,.581),(.384,.581),(.515,.627),(.476,.792),(.388,.885),
                (-.388,.885),(-.476,.792),(-.515,.627)]
        ranura = [(-.440,.925),(.440,.925),(.536,1.061),(.484,1.095),(-.484,1.095),(-.536,1.061)]
        self.fascia(1,[
            (.296,.552,"pintura",None),(.552,.906,"pintura",toma),
            (.906,1.114,"pintura",ranura),(1.114,1.123,"pintura",None),
        ],lambda u:self.capo(self.extremos[1],u))
        self.lamas(ranura,(.947,.980,1.014,1.051,1.081),-.027)
        self.lamas(toma,(.611,.85),-.036)
        for fila,z in enumerate(intervalo(.638,.821,5)):
            w=.428 if z<.751 else .402
            for i in range(-10,11):
                y=(i+.5*(fila%2))*.040
                if abs(y)>w:
                    continue
                hexagono=[(y+.021*math.cos(a),z+.017*math.sin(a))
                         for a in intervalo(0,math.tau,6)[:-1]]
                self.vivo("Celdilla hexagonal de radiador",hexagono,1,-.035,.0022,"grafito",True)
        self.insignia("mitsubishi",1.010,1,.024,escala=1.12)
        self.placa(.75,1,.025)

        for s in (-1,1):
            def lado(coords):
                return [(s*y,z) for y,z in coords]

            marco = lado([(.411,1.071),(.803,1.117),(.812,1.072),(.724,.994),(.462,.971)])
            self.faro("faro superior afilado",marco,1,[(s*.575,1.035,.032),(s*.675,1.049,.034)],.007)
            self.vivo("Firma blanca al filo superior",lado([(.456,1.071),(.60,1.081),(.735,1.102),(.792,1.116)]),
                      1,.032,.0058,"luz")
            cromado = lado([(.442,1.018),(.545,1.005),(.581,.984),(.510,.862),(.554,.657),
                            (.699,.595),(.645,.574),(.477,.610),(.428,.843)])
            self.forma("Paréntesis cromado Dynamic Shield",cromado,1,"plata",.013,.014,.022)
            carcasa = lado([(.641,.684),(.788,.706),(.794,.889),(.736,.931),(.652,.910),(.611,.868)])
            self.forma("Alojamiento del módulo vertical",carcasa,1,"grafito",.012,.013,.023)
            for z,wy in ((.752,.114),(.813,.118),(.874,.113)):
                self.sello("Lente del módulo vertical",s*.710,z,wy,.044,1,"lente",.028,.011,.016)
                self.cilindro("Punto de luz en módulo",self.cara((s*.704,z),1,.047),.013,.007,"luz","X",lados=15)
            self.vivo("Límite inciso inferior del aplique",lado([(.480,.606),(.602,.586),(.734,.614),(.796,.638)]),
                       1,.008,.0036,"sombra_chapa")
        bajo=[(-.641,.359),(-.556,.434),(-.481,.478),(.481,.478),(.556,.434),(.641,.359),
              (.533,.340),(-.533,.340)]
        self.forma("Protector inferior satinado",bajo,1,"plata",.011,.011,.025)
        self.forma("Ranura de admisión del protector",[(-.512,.375),(-.443,.444),(.443,.444),(.512,.375)],
                   1,"oscuro",.023,.009,.015)

    def posterior(self):
        self.fascia(-1,[
            (.299,.545,"pintura",None),(.545,1.271,"pintura",None),
        ],lambda u:self.cristal_base(u))
        self.panel_porton(1.344,.536,1.229)
        self.forma("Nicho de placa trasera",
                   [(-.356,.896),(.356,.896),(.286,1.032),(-.286,1.032)],-1,"sombra_chapa",.004,.005,.028)
        self.sello("Panel del nicho",0,.956,.60,.119,-1,"pintura",.009,.008)
        self.sello("Cintillo satinado bajo insignia",0,1.064,1.066,.045,-1,"plata",.010,.011,.017)
        self.insignia("mitsubishi",1.155,-1,.022,escala=.64)
        self.placa(.951,-1,.025)
        for s in (-1,1):
            def lado(coords):
                return [(y*s,z) for y,z in coords]
            perfil=lado([(.690,.552),(.765,.551),(.766,.906),(.836,1.025),
                         (.837,1.139),(.777,1.276),(.692,1.235),(.663,1.136),(.689,1.01)])
            self.forma("Caja vertical envolvente del piloto",perfil,-1,"rojo_oscuro",.009,.010,.021)
            self.forma("Lente roja y firma vertical",lado([(.707,.563),(.744,.563),(.745,.919),(.809,1.031),
                         (.817,1.132),(.766,1.238),(.714,1.206),(.686,1.132),(.716,1.02)]),
                         -1,"rojo",.023,.011,.019)
            self.forma("Inserto claro de reversa",lado([(.719,1.009),(.764,1.034),(.769,1.111),(.718,1.128)]),
                       -1,"lente",.036,.008,.010)
            mapa=lambda p,e:self.flanco(*p,s,e)
            self.relieve("Vuelta lateral roja del piloto",contorno([(-2.319,1.039),(-1.943,1.156),(-2.194,1.231),
                         (-2.319,1.245)],.019),mapa,"rojo",.008,.009,invertido=s==1)
            self.forma("Reflector bajo trasero",lado([(.451,.388),(.718,.389),(.750,.431),(.542,.445)]),
                       -1,"rojo",.018,.009,.012)
        self.forma("Difusor satinado",
                   [(-.608,.350),(-.555,.438),(.555,.438),(.608,.350)],-1,"plata",.012,.011,.015)

    def cristal_base(self,u):
        borde=self.d["bordes"][0][0]
        q=1-abs(u)**2.6
        return borde-.062*q,u*self.lado_cabina(borde,self.borde(borde)),self.borde(borde)+.020*q


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"montero_sport_blanca.json",Montero,args)


if __name__=="__main__":
    main()
