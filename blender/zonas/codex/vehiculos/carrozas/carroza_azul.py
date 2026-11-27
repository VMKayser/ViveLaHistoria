"""Coche cerrado azul: cabina abombada, ventanas altas y pescante elevado."""
import math
from kit_vehiculo_bpy import crear_caja, crear_cilindro, crear_panel
from piezas import banda, curva_2d, esfera, loft, redondeado, tubo, tubo_curvo


def construir(g, m):
    c, i, v, d = (g[k] for k in ("carroceria", "interior", "cristales", "decoracion"))
    # Vientre ovoide y cintura alta. El perímetro cambia en las tres direcciones.
    cuerpo = [
        (.845,-1.36,.074,.44,.18),(.875,-1.49,.102,.49,.17),
        (.926,-1.53,.147,.52,.15),(1.02,-1.56,.181,.547,.13),
        (1.17,-1.59,.211,.573,.115),(1.34,-1.62,.236,.585,.105),
        (1.46,-1.64,.249,.588,.095),(1.49,-1.64,.25,.587,.095),
    ]
    loft("Cabina baja abombada", [[(x,y,z+.026*abs(x+.67)) for x,y in redondeado(a,b,-w,w,r)]
                                   for z,a,b,w,r in cuerpo], m["azul"], c)
    for z, a, b, w in [(1.472,-1.64,.251,.593),(1.500,-1.639,.251,.590)]:
        tubo("Filete de cintura continuo", [(x,y,z+.026*abs(x+.67))
             for x,y in redondeado(a,b,-w,w,.103)], .0065, m["filete"], d, True)

    def ancho(z):
        return .588-.046*(z-1.49)/.88

    def posterior(z):
        return -1.644-.073*(z-1.49)/.88

    def frente(z):
        return .25-.030*(z-1.49)/.88

    z0, z1, za, zb = 1.488, 2.415, 1.588, 2.335
    a, b = -.91, .066
    for s in (-1, 1):
        def lado(x, z, extra=0):
            return (x,s*(ancho(z)+extra),z)

        def emplazar(nombre, limites, mat, grupo, extra=0, esp=.023):
            xa, xb, zl, zh = limites
            puntos = [lado(x,z,extra) for x,z in ((xa(zl),zl),(xb(zl),zl),(xb(zh),zh),(xa(zh),zh))]
            return crear_panel(nombre, puntos, mat, grupo, esp, False)

        izquierda, derecha = lambda z: a, lambda z: b
        for limites in ((posterior,izquierda,z0,z1),(derecha,frente,z0,z1),
                         (izquierda,derecha,z0,za),(izquierda,derecha,zb,z1)):
            emplazar("Capota de cuero y pilares", limites, m["cuero"], c)
        for x0,x1,t0,t1,material,radio in [
            (a-.015,b+.016,za-.017,zb+.017,"azul_borde",.037),
            (a+.030,b-.028,za+.029,zb-.024,"hierro",.012),
            (a-.075,b+.072,z0+.013,z1-.045,"filete",.0048),
        ]:
            pts = [lado(x,z,.018 if material!="filete" else .013)
                   for x,z in redondeado(x0,x1,t0,t1,.027)]
            tubo("Marco lateral", pts, radio, m[material], d, True)
        emplazar("Cristal lateral ahumado", (izquierda,derecha,za,zb), m["vidrio"], v, -.015, 0)
        p = [(-.91,1.48,.593),(.153,1.50,.590),(.132,1.16,.577),
             (.105,1.015,.547),(-.02,.971,.547),(-.78,.971,.552),
             (-.90,1.015,.554),(-.915,1.24,.585)]
        tubo("Filete perfilado de la puerta", [(x,s*(w+.007),z) for x,z,w in p],
             .0065,m["filete"],d,True)
        esfera("Montura de manilla", (.07,s*.602,1.441), (.025,.017,.026),m["laton"],d)
        tubo("Anilla de manilla", [(.07+.041*math.cos(j*math.tau/24),s*.622,
             1.393+.033*math.sin(j*math.tau/24)) for j in range(24)], .0075,m["laton"],d,True)
        # Peldaño y soporte suspendido del piso.
        tubo("Soporte del estribo", [(-.21,s*.45,.88),(-.21,s*.52,.76),
             (-.21,s*.655,.735)],.021,m["hierro"],d)
        crear_caja("Estribo ovalado", (-.21,s*.654,.738),(.22,.185,.046),m["hierro"],d,.023)
        for xx in (-.27,-.21,-.15):
            crear_caja("Ranura en estribo",(xx,s*.656,.762),(.009,.13,.004),m["piso"],d,.002)
        tubo_curvo("Asidero arqueado del pescante", [(x,s*y,z) for x,y,z in [
             (.94,.52,1.48),(1.17,.53,1.32),(1.34,.55,1.25),(1.59,.56,1.33),
             (1.76,.55,1.56),(1.69,.53,1.69),(1.50,.52,1.72),(1.38,.52,1.60),
             (1.37,.52,1.40)]],.024,m["hierro"],d)
        suelo_pescante = [(x,s*.405,z) for x,z in curva_2d([
            (.75,1.519),(.93,1.442),(1.105,1.316),(1.286,1.218),
            (1.475,1.210),(1.643,1.279),(1.818,1.357)],26)]
        banda("Sopanda curvada de reposapiés y escudo",suelo_pescante,m["hierro"],d,.104,.078)
        tubo_curvo("Montante de hierro del pescante",[(.88,s*.317,.844),(.793,s*.333,1.052),
             (.675,s*.359,1.304),(.613,s*.384,1.500)],.035,m["hierro"],d)
        tubo_curvo("Riostra delantera de asidero",[(1.373,s*.519,1.402),(1.370,s*.490,1.28),
             (1.364,s*.414,1.252)],.022,m["hierro"],d)
        tubo("Riostra posterior de asidero",[(.942,s*.518,1.482),(.934,s*.400,1.469)],.024,m["hierro"],d)
        tubo_curvo("Asidero posterior", [(x,s*.57,z) for x,z in [
             (-1.60,1.35),(-1.72,1.57),(-1.85,1.70),(-1.99,1.64),(-2.04,1.48)]],
             .024,m["hierro"],d)
        tubo_curvo("Barandilla del asiento del cochero", [(.64,s*.39,1.65),(.76,s*.447,1.91),
             (1.04,s*.443,1.92),(1.22,s*.421,1.84),(1.22,s*.412,1.68)], .018,m["hierro"],d)

    def panel_frontal(nombre,y0,y1,bajo,alto,mat,grupo,desp=0,esp=.023):
        pts = [(frente(z)+desp,y,z) for y,z in ((y0,bajo),(y1,bajo),(y1,alto),(y0,alto))]
        crear_panel(nombre,pts,mat,grupo,esp,False)

    for limites in ((-.557,-.37,z0,z1),(.37,.557,z0,z1),(-.37,.37,z0,1.75),(-.37,.37,2.306,z1)):
        panel_frontal("Montante frontal de la cabina",*limites,m["cuero"],c)
    panel_frontal("Cristal del frente",-.37,.37,1.75,2.306,m["vidrio"],v,-.018,0)
    for ya,yb,zz0,zz1,radio,mat in ((-.382,.382,1.742,2.318,.034,m["azul_borde"]),
                                     (-.347,.347,1.774,2.29,.011,m["hierro"])):
        tubo("Marco frontal de la luna",[(frente(z)+.021,y,z)
             for y,z in redondeado(ya,yb,zz0,zz1,.045)],radio,mat,d,True)
    trasera = [(posterior(z), y, z) for y,z in ((-.586,z0),(.586,z0),(.544,z1),(-.544,z1))]
    crear_panel("Cierre posterior tapizado",trasera,m["cuero"],c,.025,False)
    for inferior in (False, True):
        abajo,arriba = (.924,1.425) if inferior else (1.562,2.38)
        ancho0,ancho1 = (.39,.505) if inferior else (.47,.483)
        if inferior:
            puntos = [(interpolado_x(z,cuerpo)-.010,y*(ancho0+(ancho1-ancho0)*(z-abajo)/(arriba-abajo)),z)
                      for y,z in redondeado(-1,1,abajo,arriba,.065)]
        else:
            puntos = [(posterior(z)-.018,y*ancho0,z) for y,z in redondeado(-1,1,abajo,arriba,.066)]
        tubo("Filete posterior",puntos,.0068,m["filete"],d,True)

    techo = []
    for z,a0,b0,w,radio,arco in [
        (2.385,-1.714,.288,.594,.116,.035),(2.410,-1.735,.310,.619,.111,.045),
        (2.432,-1.722,.297,.611,.118,.058),(2.463,-1.660,.257,.551,.125,.052),
        (2.487,-1.52,.145,.376,.126,.030),(2.503,-1.36,.018,.204,.105,.015),
    ]:
        techo.append([(x,y,z+arco*(1-(y/max(w,.15))**2)) for x,y in redondeado(a0,b0,-w,w,radio)])
    loft("Capota con corona curva",techo,m["capota"],c)
    tubo("Vivo de latón de la capota",[(x,y,2.419+.043*(1-(y/.621)**2))
         for x,y in redondeado(-1.735,.310,-.621,.621,.112)], .006,m["filete"],d,True)

    for s in (-1,1):
        y = s*.647
        tubo("Ménsula de farol",[(.149,s*.543,2.293),(.269,s*.60,2.30),(.323,y,2.243),
             (.356,y,2.205)],.018,m["laton"],d)
        farol(.346,y,2.115,d,m)
    crear_caja("Piso de cabina",(-.63,0,1.004),(1.38,1.00,.058),m["piso"],i,.033)
    for x in (-1.21,-.13):
        crear_caja("Banqueta interior de tela", (x,0,1.246),(.425,.99,.169),m["tapizado"],i,.068,4)
        crear_caja("Respaldo interior de tela", (x+(-.177 if x<-.5 else .177),0,1.502),
                   (.131,.98,.47),m["tapizado"],i,.050,4)
    for s in (-1,1):
        y = s*.387
        p = [(x,y,z) for x,z in curva_2d([(.18,1.064),(.31,1.16),(.51,1.41),
                (.66,1.52),(.92,1.54),(1.15,1.51)],25)]
        banda("Costilla curvada bajo pescante",p,m["hierro"],c,.136,.109)
    crear_caja("Caja del pescante",(.916,0,1.63),(.56,.82,.21),m["cuero"],c,.048,4)
    asiento(.94,1.807,.42,.82,d,m["cuero"],m["piso"])
    respaldo = crear_caja("Respaldo inclinado de cuero",(.737,0,1.985),(.139,.834,.277),m["cuero"],d,.065,4)
    respaldo.rotation_euler.y = -.16
    tubo("Vivo del respaldo",[(.799,y,z) for y,z in redondeado(-.399,.399,1.870,2.097,.04)],
         .006,m["piso"],d,True)
    tabl = crear_caja("Reposapiés del pescante", (1.340,0,1.292),(.56,.94,.069),m["piso"],c,.019)
    tabl.rotation_euler.y = .42
    crear_caja("Tablero delantero del pescante",(1.81,0,1.535),(.074,.92,.403),m["cuero"],c,.018)
    tubo("Filete del tablero delantero",[(1.849,y,z) for y,z in
         redondeado(-.425,.425,1.365,1.699,.041)],.006,m["filete"],d,True)


def interpolado_x(z, secciones):
    from kit_vehiculo_bpy import interpolar_hermite
    return interpolar_hermite([(a,b) for a,b,*_ in secciones],z)


def asiento(x,z,fondo,ancho,grupo,cuero,vivo):
    crear_caja("Cojín abombado", (x,0,z), (fondo,ancho,.115),cuero,grupo,.054,4)
    tubo("Costura perimetral del cojín",[(a,b,z+.033) for a,b in
         redondeado(x-fondo/2+.012,x+fondo/2-.012,-ancho/2+.013,ancho/2-.013,.06)],
         .0055,vivo,grupo,True)


def farol(x,y,z,p,m):
    c = m["laton"]
    angulos = [math.tau*j/6+math.pi/6 for j in range(6)]
    def anillo(r,h):
        return [(x+r*math.cos(a),y+r*math.sin(a),z+h) for a in angulos]
    for nombre, secciones in [
        ("Pie facetado",[(.027,-.22),(.050,-.177),(.083,-.158),(.084,-.144)]),
        ("Sombrerete de latón",[(.104,.119),(.105,.135),(.082,.149),(.064,.178),(.027,.194)]),
        ("Aro de coronación",[(.046,.187),(.044,.204),(.022,.217)]),
    ]:
        loft(nombre,[anillo(r,h) for r,h in secciones],c,p)
    loft("Vidrios miel del farol",[anillo(.072,-.147),anillo(.089,.128)],m["vidrio_farol"],p)
    for p0,p1 in zip(anillo(.078,-.151),anillo(.095,.131)):
        tubo("Montante del farol",[p0,p1],.008,c,p)
    esfera("Remate del farol",(x,y,z+.227),(.024,.024,.027),c,p,12,6)
    esfera("Gota de farol",(x,y,z-.23),(.015,.015,.023),c,p,12,6)
