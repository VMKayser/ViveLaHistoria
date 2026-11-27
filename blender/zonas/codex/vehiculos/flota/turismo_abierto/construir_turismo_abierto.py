"""Turismo de cuatro puertas con capota plegada, latón y cuero."""
import math
from pathlib import Path
import sys

AQUI=Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from taller_clasicos import Clasico
from taller_lamina import contorno, ejecutar_modelo, intervalo, interpolar
from kit_vehiculo_bpy import interpolar_hermite


class Turismo(Clasico):
    def puertas(self):
        for s in (-1,1):
            mapa=lambda p,ext:self.costado(*p,s,ext)
            for x1,x0 in ((.554,-.374),(-.404,-1.339)):
                alto=1.270
                abajo=.694
                perfil=[(x0+.032,alto),(x1-.033,alto),(x1,alto-.04),
                       (x1-.035,abajo+.031),(x1-.105,abajo),
                       (x0+.055,abajo+.011),(x0,abajo+.056),(x0,alto-.034)]
                borde=contorno(perfil,.024,7)
                self.relieve("Paño estampado de puerta",borde,mapa,"carroceria",.005,.012,invertido=s==1)
                self.tubo("Junquillo de latón de puerta",[mapa(p,.009) for p in borde],.0038,
                          "laton_oscuro",cerrado=True)
                x=x1-.082
                y=mapa((x,1.190),.016)[1]
                self.bloque("Bocallave de puerta",(x,y,1.165),(.052,.018,.104),"laton_oscuro",.015,"decoracion")
                self.forja("Manilla de latón",( (x-.067,y+s*.028,1.198),(x-.014,y+s*.035,1.205),
                             (x+.048,y+s*.018,1.199)),.009,"laton")
                for z in (.783,1.164):
                    p=mapa((x0+.006,z),.013)
                    self.cilindro("Bisagra aparente de puerta",p,.012,.056,"laton_oscuro","Z",lados=12)

    def parabrisas(self):
        (x0,z0,w0),(x1,z1,w1)=self.d["meta_parabrisas"]

        def panel(u,t,ext=0):
            return (interpolar(x0,x1,t)+ext+.018*(1-u*u),u*interpolar(w0,w1,t),
                    interpolar(z0,z1,t)+.009*(1-u*u))

        self.piel("Vidrio único del parabrisas",[[panel(u,t,-.006) for t in intervalo(.028,.969,14)]
                  for u in intervalo(-.963,.963,27)],"vidrio","cristales")
        perfil=[(-1,0),(1,0),(1,1),(-1,1)]
        self.tubo("Marco del parabrisas en latón",[panel(u,t) for u,t in contorno(perfil,.037,12)],
                  .0165,"laton",cerrado=True)
        for s in (-1,1):
            px,py,pz=panel(s,.50)
            self.cilindro("Bisagra lateral de parabrisas",(px,py+s*.014,pz),.030,.047,"laton",lados=22)
            self.forja("Brazo tensor del parabrisas",[(.285,s*.581,1.302),(.433,s*.572,1.425),
                       (.483,s*.539,1.587)],.013,"laton_oscuro")
            self.bloque("Anclaje al torpedo",(.294,s*.565,1.298),(.087,.062,.048),"laton",.017,"decoracion")

    def habitaculo(self):
        self.bloque("Piso del habitáculo abierto",(-.646,0,.59),(2.50,1.023,.133),"piso",.031,"interior")
        self.bloque("Tablero de madera en torpedo",(.586,0,1.231),(.135,1.041,.176),"piso",.048,"interior")
        for y,r in ((-.258,.046),(.048,.029),(.169,.024)):
            self.cilindro("Aro de instrumento",(.511,y,1.238),r,.026,"laton","X","interior")
            self.cilindro("Esfera de instrumento",(.493,y,1.238),r*.79,.010,"lona","X","interior")
        self.banqueta(.016,1.033,1.074,.540,.368)
        self.banqueta(-1.080,1.091,1.096,.536,.368)
        self.volante((.233,.346,1.477),.189,"piso")
        for s in (-1,1):
            for x in (-.592,.050):
                self.bloque("Revestimiento interior de puerta",(x,s*.539,.951),
                             (.780,.093,.506),"cuero",.043,"interior")
                self.tubo("Costura longitudinal lateral",[(y,s*.490,1.109) for y in intervalo(x-.338,x+.337,16)],
                          .0044,"vivo","interior")
        self.forja("Palanca junto al asiento",[(.201,-.065,.714),(.132,-.077,.959),(.104,-.070,1.087)],
                   .016,"metal","interior")
        self.bola("Pomo de palanca",(.104,-.070,1.087),(.035,.032,.031),"piso","interior")

    def posterior(self):
        tabla=self.d["faldon"]

        def mapa(p,ext):
            y,z=p
            x=interpolar_hermite([(fila[0],fila[1]) for fila in tabla],z)
            return x-ext-.031*(1-(y/.56)**2),y,z

        self.tubo("Filete del tablero trasero",[mapa(p,.008) for p in
                  contorno([(-.512,.729),(.512,.729),(.536,1.234),(-.536,1.234)],.046,9)],
                  .0056,"laton_oscuro",cerrado=True)
        for s in (-1,1):
            self.piloto(-2.002,s*.503,.684,.059)
            self.forja("Soporte de piloto trasero",[(-1.908,s*.496,.531),(-1.944,s*.505,.610),
                       (-1.991,s*.504,.677)],.020,"laton_oscuro")
            for j in range(3):
                x=-1.788-.081*j
                z=1.369+.057*j
                self.forja("Brazo articulado de capota plegada",[(x+.178,s*.594,z-.122),
                    (x+.003,s*.653,z-.013),(x-.032,s*.610,z+.049)],.019,"laton_oscuro")
        for x,z,r in ((-1.855,1.383,.065),(-1.929,1.465,.069),(-1.976,1.526,.057)):
            self.forja("Dobleces de lona de capota plegada",[(x+.059,-.62,z-.007),
                       (x,-.50,z),(x,0,z+.012),(x,.50,z),(x+.059,.62,z-.007)],r,"lona")
        for y in (-.350,.350):
            self.forja("Cincha que abraza la lona",[(-2.047,y,1.555),(-2.077,y,1.481),
                       (-2.034,y,1.376),(-1.985,y,1.302)],.018,"correa")
            self.tubo("Hebilla de capota",[(-2.083,y+d,1.450+a)
                      for d,a in ((-.022,-.024),(.022,-.024),(.022,.024),(-.022,.024))],
                      .0052,"laton",cerrado=True)
        self.cilindro("Botón posterior",(-1.993,0,.717),.034,.036,"laton","X")
        self.bloque("Larguero final del turismo",(-1.905,0,.512),(.114,1.184,.072),"metal",.017)
        self.forja("Manivela bajo radiador",[(1.660,0,.630),(1.719,0,.591),(1.710,-.080,.584)],
                   .014,"metal")

    def construir(self):
        self.limusina_abierta()
        self.obstaculos.extend(self.g["carroceria"].children)
        self.faldas_y_estribos()
        self.capo_y_opticas()
        self.puertas()
        self.parabrisas()
        self.habitaculo()
        self.posterior()
        return self.conservar_pivotes()


def main(args=None):
    if args is None:
        args=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
    ejecutar_modelo(AQUI/"turismo_abierto.json",Turismo,args)


if __name__=="__main__":
    main()
