"""Construcción de bastidores, ruedas de madera y chapa clásica."""
import math
from pathlib import Path
import sys

import bpy

from taller_lamina import TallerLamina, contorno, intervalo, verificar_holgura
from kit_vehiculo_bpy import configurar_normal_goma, crear_torno, crear_vacio, interpolar_hermite

AQUI = Path(__file__).resolve().parent
sys.path.insert(0,str(AQUI.parent))
from carrozas.piezas import banda, esfera, loft, redondeado, tubo_curvo

PALETA = {
    "carroceria": ("#302c34",.34,.20), "aleta": ("#3a3338",.35,.19),
    "laton": ("#c29255",.33,.62), "laton_oscuro": ("#836044",.50,.48),
    "metal": ("#474349",.51,.47), "acero": ("#b6a7a2",.40,.66),
    "radios": ("#b48343",.40,.15), "aro": ("#785d4c",.42,.40),
    "neumatico": ("#3c3436",.83,0), "oscuro": ("#29252b",.81,0),
    "cuero": ("#5e3832",.67,0), "vivo": ("#93614d",.66,0),
    "piso": ("#514039",.84,0), "vidrio": ("#c2b7af",.19,0,.34),
    "lente": ("#edcd9d",.27,.12), "rojo": ("#a32c36",.33,.17),
    "lona": ("#c3a17b",.88,0), "correa": ("#745043",.74,0),
}


class Clasico(TallerLamina):
    def __init__(self, datos):
        mov = {
            "velocidad_maxima": 7.50, "retroceso_maximo": 1.62, "aceleracion": 1.46,
            "frenada": 2.88, "direccion_maxima": .40, "rapidez_direccion": .81,
            "velocidad_demo": 2.2, "radio_demo": 9.0,
        }
        if datos.get("tipo_direccion")=="tornamesa":
            mov.update(velocidad_maxima=4.0,aceleracion=1.0,direccion_maxima=.25,
                       tipo_direccion="tornamesa",radios_ruedas={"trasera":datos["radio_rueda"],
                       "delantera":datos["radio_rueda"]},enganche={"distancia_al_eje_delantero_m":1.72})
        datos["movimiento"]=mov
        datos["paleta"]={**PALETA,**datos["paleta"]}
        datos["acabados"]={"presupuesto_triangulos":75000,"textura_goma":True}
        super().__init__(datos)
        self.obstaculos=[]
        for nombre in ("carroceria","aleta"):
            n=self.m[nombre].node_tree.nodes["Principled BSDF"]
            n.inputs["Coat Weight"].default_value=.15
            n.inputs["Coat Roughness"].default_value=.34
        n=self.m["vidrio"].node_tree.nodes["Principled BSDF"]
        n.inputs["Specular IOR Level"].default_value=.12
        n.inputs["IOR"].default_value=1.12

    def forja(self,nombre,puntos,radio,mat,grupo="decoracion"):
        return tubo_curvo(nombre,puntos,radio,self.m[mat],self.g[grupo])

    def volumen(self,nombre,filas,mat,grupo="carroceria"):
        return loft(nombre,filas,self.m[mat],self.g[grupo])

    def banda(self,nombre,perfil,mat,ancho,alto,grupo="carroceria"):
        return banda(nombre,perfil,self.m[mat],self.g[grupo],ancho,alto)

    def bola(self,nombre,p,escala,mat,grupo="decoracion"):
        return esfera(nombre,p,escala,self.m[mat],self.g[grupo])

    def ruedas(self):
        configurar_normal_goma(self.m["neumatico"],AQUI.parent/"texturas/Rubber004_1K-JPG_NormalGL.jpg",.20)
        trasero,delantero=self.d["ejes"]
        r=self.d["radio_rueda"]
        via=self.d["semivia_ruedas"]
        raiz=self.g["raiz"]
        if self.d.get("tipo_direccion")=="tornamesa":
            self.g["tornamesa_delantera"]=crear_vacio("tornamesa_delantera",(delantero,0,r),raiz)
        for etapa,x in (("trasera",trasero),("delantera",delantero)):
            padre=self.g["tornamesa_delantera"] if etapa=="delantera" and "tornamesa_delantera" in self.g else raiz
            for signo,lado in ((-1,"derecha"),(1,"izquierda")):
                sufijo=f"{etapa}_{lado}"
                y=signo*via
                grupo="rueda_"+sufijo
                if etapa=="delantera":
                    dn="direccion_"+sufijo
                    p=(0,y,0) if padre!=raiz else (x,y,r)
                    self.g[dn]=crear_vacio(dn,p,padre)
                    self.g[grupo]=crear_vacio(grupo,padre=self.g[dn])
                else:
                    self.g[grupo]=crear_vacio(grupo,(x,y,r),raiz)
                bpy.context.view_layer.update()
                self.tornear_rueda(x,y,r,signo,grupo)

    def tornear_rueda(self,x,y,r,s,grupo):
        padre=self.g[grupo]
        ancho,ra=self.d["ancho_rueda"]/2,self.d["radio_aro"]
        perfil=[(ra*.974,-.73),(r*.866,-.97),(r*.934,-1),(r*.979,-.84),
                (r,-.56),(r,-.39),(r-.004,-.33),(r-.004,-.25),(r,-.21),
                (r,-.09),(r-.004,-.053),(r-.004,.053),(r,.09),(r,.21),
                (r-.004,.25),(r-.004,.33),(r,.39),(r,.56),
                (r*.979,.84),(r*.934,1),(r*.866,.97),(ra*.974,.73)]
        crear_torno("Neumatico radial",[(rad,v*ancho) for rad,v in perfil],
                    x,y,r,s,self.m["neumatico"],padre,48,dibujo_banda=(r-.001,ancho*.60,.0030),con_uv=True)
        aro=[(ra*.884,-.65),(ra*.98,-.72),(ra*1.018,-.56),(ra*1.027,.42),
             (ra*1.006,.76),(ra*.963,.875),(ra*.905,.685),(ra*.88,.46)]
        crear_torno("Llanta de acero torneada",[(rad,v*ancho) for rad,v in aro],
                    x,y,r,s,self.m["aro"],padre,48,cerrado=True)
        madera=[(ra*.889,-.52),(ra*.978,-.56),(ra*.99,.51),(ra*.964,.705),
                (ra*.926,.715),(ra*.89,.48)]
        crear_torno("Corona de madera de radios",[(rad,v*ancho) for rad,v in madera],
                    x,y,r,s,self.m["radios"],padre,48,cerrado=True)
        filo=[(ra*.972,.68),(ra*.986,.70),(ra*.996,.685),(ra*.989,.635)]
        crear_torno("Banda brillante de aro",[(rad,v*ancho) for rad,v in filo],
                    x,y,r,s,self.m["laton_oscuro"],padre,48,cerrado=True)
        n=self.d["radios"]
        for i in range(n):
            a=(i+.35)*math.tau/n
            ca,sa=math.cos(a),math.sin(a)
            filas=[]
            for d,grueso,frente in ((.052,.022,.13),(.098,.021,.23),
                      (ra*.51,.014,.20),(ra*.79,.013,.28),(ra*.927,.022,.42)):
                filas.append([(x+ca*d-sa*grueso*math.cos(t),y+s*(frente*ancho+ancho*.35*math.sin(t)),
                               r+sa*d+ca*grueso*math.cos(t)) for t in intervalo(0,math.tau,8)[:-1]])
            self.volumen("Radio torneado de madera",filas,"radios",grupo)
        for nombre,rad,largo,pos,mat in (
                ("Tambor posterior del cubo",.097,.056,-.029,"metal"),
                ("Cubo grueso con brida",.083,.107,.010,"laton_oscuro"),
                ("Arandela torneada de cubo",.053,.027,.062,"laton"),
                ("Tuerca hexagonal de cubo",.031,.027,.083,"metal")):
            self.cilindro(nombre,(x,y+s*pos,r),rad,largo,mat,grupo=grupo,lados=6 if "hexagonal" in nombre else 28)
        for i in range(6):
            a=i*math.tau/6
            self.cilindro("Remache de brida",(x+.065*math.cos(a),y+s*.064,r+.065*math.sin(a)),
                          .0075,.009,"acero",grupo=grupo,lados=10)

    def chasis(self):
        r=self.d["radio_rueda"]
        via=self.d["semivia_ruedas"]
        t,d=self.d["ejes"]
        rodado="tornamesa_delantera" in self.g
        z_larguero=r+.305 if rodado else .502
        carril=.45 if rodado else .367
        for s in (-1,1):
            perfil=[(x,s*carril,z_larguero+.055*((x-(t+d)/2)/(d-t))**2)
                    for x in intervalo(t-.34,d+.28,22)]
            self.banda("Larguero de acero curvado",perfil,"metal",.074,.067)
        for x in (t-.19,(t+d)/2,d+.13):
            self.bloque("Travesaño estructural",(x,0,z_larguero+.046),(.087,2*carril+.066,.064),"metal",.013)
        for tramo,x in (("trasero",t),("delantero",d)):
            grupo="tornamesa_delantera" if tramo=="delantero" and rodado else "carroceria"
            self.cilindro("Eje "+tramo,(x,0,r),.041,2*via-.064,"metal",grupo=grupo)
            self.bola("Diferencial" if tramo=="trasero" else "Nudo central de eje",
                      (x,0,r),(.099,.127,.091),"metal",grupo)
            for s in (-1,1):
                y=s*carril
                for i in range(4):
                    a=.30-i*.040
                    z=r+.077+i*.017
                    self.banda("Lámina de ballesta "+tramo,[(p,y,z+.072*((p-x)/a)**2)
                                for p in intervalo(x-a,x+a,14)],"metal",.039,.013,grupo)
                self.bloque("Abrazadera de ballesta",(x,y,r+.137),(.112,.056,.158),"oscuro",.010,grupo)
                for lado in (-1,1):
                    self.bloque("Gemela de ballesta",(x+lado*.269,y,r+.201),(.041,.052,.145),"metal",.010,grupo)
            self.cilindro("Tirante transversal de eje",(x-.126,0,r+.039),.016,2*via-.16,"laton_oscuro",grupo=grupo)
        if rodado:
            for radio,z in ((.247,r+.229),(.276,r+.263),(.091,r+.297)):
                self.cilindro("Corona de giro",(d,0,z),radio,.035,"metal","Z","tornamesa_delantera",lados=31)

    def conservar_pivotes(self):
        self.ruedas()
        self.chasis()
        return {"angulos_direccion_verificados":verificar_holgura(self,self.obstaculos)}

    def limusina_abierta(self):
        """Vientre de carrocería y canto del compartimiento con interior abierto."""
        filas=[]
        for z,x0,x1,w,rf in self.d["faldon"]:
            filas.append([(x,y,z+.018*(abs(x-(x0+x1)/2)/(x1-x0))**2)
                          for x,y in redondeado(x0,x1,-w,w,rf,7)])
        self.piel("Casco curvo de carrocería",filas,"carroceria",cerrar_v=True,invertir=True)
        xy=self.d["faldon"][-1]
        z,x0,x1,w,r=xy
        borde_int=redondeado(x0+.054,x1-.056,-w+.048,w-.048,r,7)
        self.piel("Canto y revestimiento al interior",[
            [p,(x,y,p[2]+.013),(x,y*.965,z-.175)]
            for p,(x,y) in zip(filas[-1],borde_int)],"carroceria",cerrar_u=True)
        self.tapa("Cierre inferior del casco",filas[0],"oscuro","interior",True)

    def costado(self,x,z,s,esp=0):
        tabla=self.d["faldon"]
        w=interpolar_hermite([(r[0],r[3]) for r in tabla],z)
        extremos=[interpolar_hermite([(r[0],r[i]) for r in tabla],z) for i in (1,2)]
        curva=interpolar_hermite([(r[0],r[4]) for r in tabla],z)
        esquina=min(x-extremos[0],extremos[1]-x)
        ajuste=max(0,curva-esquina)
        y=w-curva+math.sqrt(max(0,curva**2-ajuste**2))
        return x,s*(y+esp),z

    def faldas_y_estribos(self):
        radio=self.d["radio_rueda"]
        via=self.d["semivia_ruedas"]
        t,d=self.d["ejes"]
        cerrado=self.d["id"]=="model_t_coupe"
        for s in (-1,1):
            for i,eje in enumerate((t,d)):
                parte_del=i==1
                rec=self.d["fender"][i]
                limite=(.47,math.pi-.113) if parte_del else (.126,math.pi-.43)
                filas=[]
                for a in intervalo(*limite,42):
                    x=eje+(radio+rec)*math.cos(a)
                    z=radio+(radio+rec)*math.sin(a)
                    fondo=abs((a-(limite[0]+limite[1])/2)/(limite[1]-limite[0])*2)
                    centro=via-(.022 if cerrado else .005)
                    semiancho=.135-.018*fondo**4
                    filas.append([(x,s*(centro+w*semiancho),z-.037*abs(w)**2.5)
                                  for w in intervalo(-1,1,11)])
                al=self.piel("Aleta delantera ondulada" if parte_del else "Aleta posterior ondulada",
                             filas,"aleta",invertir=s==(-1 if parte_del else 1))
                self.obstaculos.append(al)
                for j in (0,-1):
                    tira=[f[j] for f in filas]
                    labio=self.piel("Labio de borde de aleta",[
                         [p,(p[0],p[1]-s*.010 if j else p[1]+s*.010,p[2]-.021)]
                         for p in tira],"aleta",invertir=j==0)
                    self.obstaculos.append(labio)
                    self.tubo("Filete del guardabarros",[(x,y-s*.004 if j else y+s*.005,z+.003)
                              for x,y,z in tira],.0037,"laton_oscuro")
                for extremo in (0,-1):
                    self.piel("Remate de guardabarros",[
                        [p,(p[0],p[1],p[2]-.019)] for p in filas[extremo]],"aleta",invertir=extremo==0)
            a=t+(radio+self.d["fender"][0])*math.cos(.126)-.018
            b=d-(radio+self.d["fender"][1])*math.cos(.113)+.021
            y=s*(via-.108)
            self.banda("Estribo perfilado entre las aletas",
                       [(x,y,.463+.035*abs((2*x-a-b)/(b-a))**5) for x in intervalo(a,b,30)],
                       "aleta",.283,.052)
            for cambio in (-.127,.127):
                self.tubo("Ribete de estribo",[(x,y+cambio,.519+.026*abs((2*x-a-b)/(b-a))**5)
                             for x in intervalo(a+.011,b-.012,23)],.0049,"laton_oscuro")
            for x in ((-.58,.084) if not cerrado else (-.17,)):
                self.bloque("Pisadera de metal",(x,y+s*.032,.522),(.312,.144,.022),"acero",.012,"decoracion")
                for off in (-.038,0,.038):
                    self.tubo("Ranura antideslizante",[(x+u,y+s*.032+off,.535) for u in (-.133,.133)],.0027,"metal")

    def capo_y_opticas(self):
        claves=self.d["capo"]
        x0,x1=claves[0][0],claves[-1][0]
        fs=[[(fila[0],fila[i]) for fila in claves] for i in (1,2)]
        z_base=.735
        secciones=[]
        for x in intervalo(x0,x1,31):
            w,z=(interpolar_hermite(p,x) for p in fs)
            secciones.append([(x,(w*(.94+.06*math.sin(t)))*math.cos(t),
                               z_base+(z-z_base)*math.sin(t)**.72)
                               for t in intervalo(0,math.pi,37)])
        self.piel("Capó abovedado y estrechado al frente",secciones,"carroceria")
        self.tapa("Tabique posterior de motor",secciones[0],"piso","carroceria",True)
        def superficie_y(x,altura):
            w,z=(interpolar_hermite(p,x) for p in fs)
            seno=max(0,min(1,(altura-z_base)/(z-z_base)))**(1/.72)
            return w*(.94+.06*seno)*math.sqrt(max(0,1-seno*seno))

        for s in (-1,1):
            for z in (.802,1.102):
                ps=[(x,s*(superficie_y(x,z)+.0027),z) for x in intervalo(x0+.013,x1-.007,31)]
                self.tubo("Junta longitudinal de capó",ps,.0033,"laton_oscuro")
            for x in intervalo(x0+.137,x1-.128,13):
                zs=intervalo(.827,1.064,13)
                self.tubo("Celosía oscura del respiradero",[(x,s*(superficie_y(x,z)+.0058),z)
                         for z in zs],.0071,"oscuro")
                self.tubo("Borde levantado de respiradero",[(x-.008,s*(superficie_y(x,z)+.0050),z)
                         for z in zs],.0032,"metal")
        r=self.d["radio_rueda"]
        w=claves[-1][1]*.95
        ztop=claves[-1][2]+.013
        self.radiador(x1+.011,w,.682,ztop)
        for s in (-1,1):
            cx=x1+.048
            y=s*(w+.153)
            z=(.997 if self.d["id"]=="turismo_abierto" else .943)
            self.farol((cx,y,z),.122)
            self.forja("Soporte articulado de farol",[(cx-.119,s*(w+.078),.588),
                       (cx-.139,y,.699),(cx-.117,y,z-.058)],.024,"laton_oscuro")
        self.cilindro("Cuello de tapón de radiador",(x1-.046,0,ztop+.017),.031,.045,"laton_oscuro","Z")
        self.bola("Tapón torneado de radiador",(x1-.046,0,ztop+.047),(.044,.038,.018),"laton")
        self.bloque("Cierre del inferior de motor",((x1+x0)/2,0,r+.11),(x1-x0,.62,.175),"metal",.032,"interior")

    def radiador(self,x,w,abajo,arriba):
        perfil=[(-w+.032,abajo),(w-.032,abajo),(w,abajo+.044),(w,arriba-.153),
                (w*.85,arriba-.064),(w*.5,arriba-.017),(0,arriba),
                (-w*.5,arriba-.017),(-w*.85,arriba-.064),(-w,arriba-.153),(-w,abajo+.044)]
        exterior=contorno(perfil,.028,5)
        centro=(0,(abajo+arriba)/2)
        filas=[]
        for y,z in exterior:
            approach=lambda q,prof:(x+prof, q*y,centro[1]+q*(z-centro[1]))
            filas.append([approach(q,p) for q,p in ((1,-.031),(1,0),(.989,.027),
                         (.935,.041),(.864,.032),(.844,.016),(.836,-.036))])
        self.piel("Marco alto de radiador de latón",filas,"laton",cerrar_u=True)
        self.tapa("Rejilla hundida y oscura",[f[-1] for f in filas],"oscuro","carroceria")
        for y in intervalo(-w*.772,w*.772,24):
            top=arriba-.071-.105*(abs(y)/w)**2
            self.tubo("Nervio de rejilla",[(x-.014,y,z) for z in (abajo+.048,top)],.0024,"metal")
        for z in intervalo(abajo+.052,arriba-.139,18):
            self.tubo("Alambre transversal de parrilla",[(x-.012,y,z) for y in (-w*.76,w*.76)],
                      .0019,"metal")

    def farol(self,p,radio):
        x,y,z=p
        self.bola("Carcasa convexa de faro",(x-.068,y,z),(.093,radio*.965,radio*.965),"laton_oscuro")
        self.cilindro("Cierre metálico de faro",(x-.009,y,z),radio,.021,"laton","X",lados=38)
        self.bola("Lente abombada del faro",(x+.018,y,z),(.034,radio*.883,radio*.883),"lente")
        self.tubo("Aro de latón del faro",[(x+.022,y+radio*.937*math.cos(a),z+radio*.937*math.sin(a))
                 for a in intervalo(0,math.tau,37)[:-1]],.008,"laton",cerrado=True)
        for b in (-.060,-.035,0,.035,.060):
            alto=.87*math.sqrt(radio**2-b**2)
            self.tubo("Prisma tallado en óptica",
                      [(x+.018+.037*math.sqrt(max(0,1-(b*b+a*a)/(radio**2))),y+b,z+a)
                       for a in intervalo(-alto,alto,10)],.0019,"lente")

    def piloto(self,x,y,z,r):
        self.cilindro("Copa de luz trasera",(x,y,z),r,.036,"laton","X",lados=28)
        self.bola("Óptica roja posterior",(x-.024,y,z),(.022,r*.844,r*.844),"rojo")
        self.tubo("Junquillo de piloto",[(x-.032,y+r*.91*math.cos(a),z+r*.91*math.sin(a))
                  for a in intervalo(0,math.tau,29)[:-1]],.006,"laton",cerrado=True)

    def banqueta(self,x,z,ancho,prof,alto,grupo="interior"):
        w=ancho/2
        asiento=[]
        for dz,anchura,largo in ((-.068,.82,.79),(-.047,.96,.93),(-.008,1,1),
                                  (.040,.982,.955),(.066,.93,.887),(.079,.80,.75)):
            asiento.append([(px,y,z+dz+.012*(1-(y/w)**2)) for px,y in
                            redondeado(x-prof*largo/2,x+prof*largo/2,-w*anchura,w*anchura,.074,6)])
        self.volumen("Cojín de cuero con corona",asiento,"cuero",grupo)
        respaldo=[]
        for t,g,espesor in ((.0,.903,.133),(.13,.987,.150),(.38,1,.159),(.66,.985,.144),
                           (.86,.935,.124),(.96,.885,.092),(1,.773,.055)):
            cx=x-prof*.35-.069*t
            zh=z+.072+alto*t
            ring=redondeado(cx-espesor/2,cx+espesor/2,-w*g,w*g,min(.043,espesor*.40),6)
            respaldo.append([(px+.008*(1-(y/w)**2),y,zh+.016*(1-(y/w)**2)) for px,y in ring])
        self.volumen("Respaldo de cuero abombado",respaldo,"cuero",grupo)
        for y in intervalo(-w*.804,w*.804,11):
            perfil=[]
            for t,esp in ((.048,.142),(.22,.153),(.40,.159),(.64,.146),(.84,.128),(.941,.099),(.98,.066)):
                cx=x-prof*.35-.069*t
                px=cx+esp/2+.010*(1-(y/w)**2)
                perfil.append((px+.0035,y,z+.073+alto*t+.016*(1-(y/w)**2)))
            self.tubo("Canal vertical del tapizado",perfil,.0063,"vivo",grupo)
        self.tubo("Vivo del cojín",[(x+prof*.452,y,z+.047+.014*(1-(y/w)**2))
                  for y in intervalo(-w*.886,w*.886,22)],.0067,"vivo",grupo)

    def volante(self,p,radio,mat="piso"):
        x,y,z=p
        self.tubo("Aro de volante vintage",[(x+.56*radio*math.sin(a),y+radio*math.cos(a),
                 z+.828*radio*math.sin(a)) for a in intervalo(0,math.tau,41)[:-1]],.016,mat,"interior",True)
        self.forja("Columna inclinada de dirección",[(x,y,z),(x+.134,y,z-.148),(x+.338,y,z-.342)],.021,"metal","interior")
        for a in (.18,2.26,4.37):
            self.tubo("Radio de volante",[(x,y,z),(x+.54*radio*math.sin(a),y+radio*.98*math.cos(a),
                       z+.813*radio*math.sin(a))],.013,"laton_oscuro","interior")
        self.bola("Botón central del volante",(x-.01,y,z),(.028,.039,.037),"laton","interior")
