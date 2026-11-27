"""Model T coupé de cabina alta, madera torneada y radiador de latón."""
import math
from pathlib import Path
import sys

AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from taller_clasicos import Clasico, redondeado
from taller_lamina import contorno, ejecutar_modelo, intervalo, interpolar, rectangulo
from kit_vehiculo_bpy import interpolar_hermite


class Coupe(Clasico):
    def cabina(self):
        base,alto=1.428,2.058
        bordes=[(-1.498,-1.569),(-1.242,-1.284),(-.444,-.450),(.486,.426)]
        porciones=[
            [(-1.442,1.490),(-1.286,1.489),(-1.319,1.977),(-1.493,1.976)],
            [(-1.204,1.492),(-.492,1.492),(-.504,1.987),(-1.247,1.978)],
            [(-.411,1.489),(.409,1.489),(.355,1.961),(-.410,1.981)]
        ]
        for s in (-1,1):
            def mapa(p,ext):
                x,z=p
                q=(z-base)/(alto-base)
                w=.590-.035*q+.010*math.sin(math.pi*q)
                w-=.026*((x+.562)/1.08)**4
                return x,s*(w+ext),z
            for i,(a,b,ventana) in enumerate(zip(bordes,bordes[1:],porciones)):
                exterior=contorno([(a[0],base),(b[0],base),(b[1],alto),(a[1],alto)],0,5)
                hueco=contorno(ventana,.040,5)
                self.ventana(("custodia lateral fija","ventana lateral del salón","ventana de puerta")[i],
                             exterior,hueco,mapa,"carroceria","laton_oscuro",s==1)
                self.tubo("Junquillo interior satinado",[mapa(p,.005) for p in hueco],.0042,
                          "metal",cerrado=True)
            self.tubo("Cintillo lateral bajo el vidrio",[mapa((x,1.431),.011)
                       for x in intervalo(-1.493,.481,38)],.011,"laton_oscuro")
            self.tubo("Puente entre cabina y casco",[(x,s*interpolar(.579,.548,t),1.431) for t in
                       intervalo(0,1,21) for x in [interpolar(-1.48,.485,t)]],.009,"carroceria")

        # Visera frontal con doble curva, y techo rígido con hombro redondeado.
        a,b=-1.608,.463
        anillos=[]
        for z,x0,x1,w,r,corona in [
                (2.037,a+.017,b-.019,.561,.083,.013),(2.056,a-.022,b+.032,.591,.090,.023),
                (2.092,a-.029,b+.037,.599,.097,.028),(2.124,a-.010,b+.013,.574,.095,.026),
                (2.144,a+.046,b-.037,.521,.103,.017),(2.151,a+.171,b-.131,.395,.104,.010)]:
            anillos.append([(x,y,z+corona*(1-(y/w)**2)) for x,y in redondeado(x0,x1,-w,w,r,6)])
        self.volumen("Techo cerrado de hombros curvos",anillos,"aleta")
        self.tubo("Vivo satinado bajo goterón",anillos[1],.0053,"laton_oscuro",cerrado=True)
        for s in (-1,1):
            self.tubo("Canalón de costado",[(x,s*.587,2.078+.018*math.sin(math.pi*t))
                      for t in intervalo(0,1,31) for x in [interpolar(-1.473,.409,t)]],.011,"carroceria")
        self.cristal_extremo(1,bordes[-1],base,alto)
        self.cristal_extremo(-1,bordes[0],base,alto)
        self.piel("Visera frontal inclinada",[
            [(interpolar(.429,.573,t)-.033*(abs(u)**3),u*(.55-.014*t),
              2.045-.057*t+.022*(1-u*u)) for t in intervalo(0,1,10)] for u in intervalo(-1,1,34)],
            "aleta")
        self.tubo("Refuerzo del borde de la visera",[(.573-.033*abs(u)**3,u*.536,1.988+.022*(1-u*u))
                  for u in intervalo(-1,1,32)],.011,"laton_oscuro")

    def cristal_extremo(self,s,borde,base,alto):
        x0,x1=borde

        def mapa(p,ext):
            u,t=p
            w=interpolar(.566,.538,t)
            z=interpolar(base,alto,t)+.011*(1-u*u)
            x=interpolar(x0,x1,t)+s*.040*(1-abs(u)**2.7)
            return x+s*ext,u*w,z

        exterior=contorno(rectangulo(0,.5,2,1),0,8)
        hueco=rectangulo(0,.497,1.80,.804) if s>0 else rectangulo(0,.530,1.204,.560)
        interiores=contorno(hueco,.076 if s>0 else .051,8)
        self.ventana("parabrisas del coupé" if s>0 else "luneta cuadrangular posterior",
                     exterior,interiores,mapa,"carroceria","laton_oscuro",s<0)
        self.tubo("Junquillo de vidrio frontal" if s>0 else "Junquillo de luneta",
                  [mapa(p,.007) for p in interiores],.0043,"metal",cerrado=True)
        if s>0:
            self.forja("Limpiaparabrisas del conductor",[mapa((.34,.102),.021),
                        mapa((.296,.210),.022),mapa((.164,.229),.020)],.0055,"metal")
            self.tubo("Escobilla de parabrisas",[mapa((v,.220+.066*v),.020)
                      for v in intervalo(-.05,.36,14)],.0074,"oscuro")

    def puertas(self):
        for s in (-1,1):
            mapa=lambda p,ext:self.costado(*p,s,ext)
            perfil=[(-.441,1.424),(.476,1.423),(.495,1.364),(.474,.704),(.427,.628),
                    (-.358,.627),(-.432,.682),(-.446,1.077)]
            bordes=contorno(perfil,.041,8)
            self.relieve("Chapa de puerta del coupé",bordes,mapa,"carroceria",.006,.014,invertido=s==1)
            self.tubo("Junta de puerta perfilada",[mapa(p,.010) for p in bordes],.0039,
                      "laton_oscuro",cerrado=True)
            x=-.349
            y=mapa((x,1.349),.022)[1]
            self.bloque("Placa de cerradura",(x,y,1.334),(.040,.018,.069),"laton_oscuro",.013,"decoracion")
            self.forja("Manilla en fundición de latón",[(x-.057,y+s*.013,1.341),
                        (x+.006,y+s*.039,1.349),(x+.067,y+s*.018,1.345)],.010,"laton")
            for z in (.758,1.324):
                self.cilindro("Bisagra de puerta",mapa((.452,z),.020),.013,.053,"laton_oscuro","Z",lados=14)

    def habitaculo(self):
        self.bloque("Piso de cabina",(-.536,0,.617),(1.840,1.003,.147),"piso",.041,"interior")
        self.bloque("Tablero alto de instrumentos",(.370,0,1.301),(.157,1.006,.182),"piso",.052,"interior")
        self.banqueta(-.218,1.028,1.014,.50,.372)
        self.banqueta(-1.086,1.169,1.002,.400,.325)
        self.volante((.087,.335,1.344),.183,"piso")
        for s in (-1,1):
            self.bloque("Forro oscuro bajo ventana",(-.523,s*.514,1.181),(1.610,.074,.423),
                        "cuero",.033,"interior")
        self.bloque("Espejo interior del coupé",(.372,0,1.943),(.057,.205,.059),
                     "metal",.018,"interior")
        self.forja("Palanca larga de cambio",[(.047,-.091,.715),(.012,-.098,1.007),
                   (-.018,-.094,1.130)],.013,"metal","interior")
        self.bola("Pomo de cambio",(-.018,-.094,1.130),(.033,.031,.032),"piso","interior")

    def defensas(self):
        for z in (.439,.521):
            filas=[]
            for y in intervalo(-.800,.800,40):
                x=1.70+.111*(1-(y/.8)**2)
                h=z+.028*abs(y/.8)**3
                filas.append([(x-.044,y,h-.024),(x+.003,y,h-.027),(x+.017,y,h-.013),
                              (x+.019,y,h+.016),(x+.003,y,h+.026),(x-.045,y,h+.019)])
            self.volumen("Barra frontal de defensa de latón",filas,"laton")
            for s in (-1,1):
                self.cilindro("Remache de defensa",(1.812,s*.447,z+.009),.013,.022,"metal","X",lados=14)
        for s in (-1,1):
            self.forja("Tirante hacia defensa",[(1.375,s*.315,.486),(1.572,s*.435,.483),
                       (1.803,s*.454,.484)],.023,"metal")
            self.bloque("Puente vertical de defensa",(1.812,s*.437,.484),
                         (.050,.087,.140),"laton_oscuro",.009,"decoracion")
        self.bloque("Barra posterior del bastidor",(-1.612,0,.554),(.091,1.144,.081),"metal",.015)
        self.piloto(-1.669,0,.628,.071)
        self.forja("Montura central de lámpara",[(-1.574,0,.552),(-1.613,0,.586),(-1.658,0,.634)],
                   .019,"laton_oscuro")
        for z in (.701,1.429):
            self.tubo("Vivo horizontal de trasera",[(-1.518-.048*(1-(y/.56)**2),y,z)
                      for y in intervalo(-.550,.550,29)],.0073,"laton_oscuro")

    def construir(self):
        self.limusina_abierta()
        self.obstaculos.extend(self.g["carroceria"].children)
        self.faldas_y_estribos()
        self.capo_y_opticas()
        self.cabina()
        self.puertas()
        self.habitaculo()
        self.defensas()
        return self.conservar_pivotes()


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"model_t_coupe.json",Coupe,args)


if __name__=="__main__":
    main()
