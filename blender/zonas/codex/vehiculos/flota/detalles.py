"""Frentes y accesorios según las seis referencias; sin decidir elementos al azar."""
import math
from acabados_bronco import contorno_redondeado


def ovalo(t,nombre,x,y,z,ry,rz,mat,radio=.006):
    puntos=[(x,y+ry*math.cos(math.tau*i/48),z+rz*math.sin(math.tau*i/48)) for i in range(48)]
    t.tubo(nombre,puntos,radio,mat,cerrado=True)


def emblema(t,x,z,trasero=False):
    marca=t.d['marca']
    if marca=='mitsubishi':
        for i in range(3):
            a=math.tau*i/3
            yz=[(0,0),(.026,.045),(0,.10),(-.026,.045)]
            t.panel('Diamante Mitsubishi',[(x,y*math.cos(a)-zz*math.sin(a),z+y*math.sin(a)+zz*math.cos(a)) for y,zz in yz],'cromo','decoracion')
    elif marca=='ford':
        t.caja('Base oval Ford',(x,0,z),(.025,.16,.065),'azul_logo',.03,'decoracion')
        ovalo(t,'Borde emblema Ford',x+(-.015 if trasero else .015),0,z,.078,.030,'cromo',.004)
    else:
        ovalo(t,'Emblema aro',x,0,z,.065,.046,'cromo')
        if marca=='toyota':
            ovalo(t,'Emblema interior vertical',x,0,z,.024,.043,'cromo',.004)
            ovalo(t,'Emblema interior horizontal',x,0,z+.014,.053,.021,'cromo',.004)
        else:
            t.tubo('Emblema barra',[(x,-.058,z),(x,.058,z)],.009,'cromo')


def cara(t,nombre,perfil,x,mat):
    """Placa en el frente, con arqueo transversal de la cara del coche."""
    vs=[(x-.035*(y/(t.d['ancho']/2))**2,y,z) for y,z in perfil]
    return t.panel(nombre,vs,mat,'decoracion')


def contorno(t,nombre,perfil,x,radio=.010,mat='cromo'):
    t.tubo(nombre,[(x-.035*(y/(t.d['ancho']/2))**2,y,z) for y,z in perfil],radio,mat,cerrado=True)


def faro(t,perfil,x,nombre='Faro'):
    perfil=contorno_redondeado(perfil,.018,4)
    cara(t,nombre+' caja',perfil,x,'oscuro')
    cy=sum(p[0] for p in perfil)/len(perfil)
    cz=sum(p[1] for p in perfil)/len(perfil)
    dentro=[(cy+(y-cy)*.88,cz+(z-cz)*.78) for y,z in perfil]
    cara(t,nombre+' reflector',dentro,x+.009,'faro')
    contorno(t,nombre+' labio',perfil,x+.012,.006,'cromo')
    # Grabado de lente legible sin textura fotográfica ni luz horneada.
    ymin,ymax=min(y for y,z in dentro),max(y for y,z in dentro)
    for u in [.28,.50,.72]:
        y=ymin+(ymax-ymin)*u
        t.tubo('Estría de óptica',[(x+.014,y,cz-.021),(x+.014,y,cz+.021)],.0025,'cromo')


def frente(t):
    d=t.d
    f=d['secciones'][-1][0]+.015
    w=d['ancho']/2
    h=d['altura_faros']
    estilo=d['frente']
    color=d['parachoques']
    color={'gris':'gris','cromo':'cromo','pintura':'pintura','oscuro':'oscuro'}[color]
    alto=.25 if estilo in ['dynamic_shield','hilux','ecosport'] else .20
    z=d['bajo']+.13
    if estilo=='clasico':
        z=d['bajo']+.25
        alto=.29
    t.caja('Soporte curvo del frente',(f-.085,0,h),(.16,w*1.94,.22),'pintura',.055)
    t.caja('Parachoques delantero',(f-.01,0,z),(.23,w*1.92,alto),color,.075)
    # Rejilla inferior siempre hundida en su marco; sin matrícula flotante.
    t.caja('Toma inferior',(f+.117,0,z+.012),(.018,.80,.105),'oscuro',.035,'decoracion')
    if estilo=='dynamic_shield':
        p=[(-.62,1.17),(.62,1.17),(.47,.99),(.49,.84),(.65,.68),(-.65,.68),(-.49,.84),(-.47,.99)]
        cara(t,'Parrilla Dynamic Shield',p,f+.014,'oscuro')
        for zz,ancho in [(1.11,.60),(1.04,.55),(.95,.49),(.87,.51),(.79,.56),(.72,.60)]:
            t.tubo('Lama de parrilla',[ (f+.035,-ancho,zz),(f+.035,ancho,zz)],.012,'gris')
        for s in [-1,1]:
            t.tubo('Cromado Dynamic Shield',[(f+.034,s*.78,1.18),(f+.05,s*.61,1.10),(f+.05,s*.52,.94),(f+.05,s*.59,.78),(f+.035,s*.79,.73)],.028,'cromo')
            p=[(s*.57,1.19),(s*.84,1.22),(s*.82,1.13),(s*.56,1.11)]
            faro(t,p,f+.034,'Óptica superior fina')
            p=[(s*.66,1.035),(s*.82,1.05),(s*.82,.81),(s*.65,.82)]
            cara(t,'Caja óptica vertical',p,f+.018,'oscuro')
            for zz in [.99,.92,.85]:
                faro(t,[(s*.68,zz+.023),(s*.79,zz+.023),(s*.79,zz-.023),(s*.68,zz-.023)],f+.029,'Módulo óptico inferior')
    elif estilo=='ecosport':
        p=[(-.44,1.01),(.44,1.01),(.57,.89),(.49,.68),(-.49,.68),(-.57,.89)]
        cara(t,'Parrilla hexagonal EcoSport',p,f+.026,'oscuro')
        contorno(t,'Borde de parrilla',p,f+.035,.012,'gris')
        for zz in [.72,.78,.84,.90,.96]:
            t.tubo('Lama horizontal EcoSport',[(f+.04,-.45,zz),(f+.04,.45,zz)],.012,'gris')
        for s in [-1,1]:
            faro(t,[(s*.40,1.12),(s*.80,1.16),(s*.83,1.02),(s*.55,1.00)],f+.025)
            t.caja('Alojamiento antiniebla',(f+.035,s*.70,.73),(.045,.21,.18),'oscuro',.065,'decoracion')
            t.cilindro('Aro antiniebla',(f+.068,s*.70,.73),.063,.02,'cromo','X',32,'decoracion')
            t.cilindro('Lente antiniebla',(f+.081,s*.70,.73),.048,.012,'faro','X',32,'decoracion')
    elif estilo=='hilux':
        p=[(-.48,1.21),(.48,1.21),(.54,1.06),(.43,.86),(-.43,.86),(-.54,1.06)]
        cara(t,'Parrilla Hilux',p,f+.015,'oscuro')
        contorno(t,'Marco cromado parrilla',p,f+.026,.022,'cromo')
        for zz in [.92,.99,1.06,1.13]:
            t.tubo('Lama Hilux',[(f+.033,-.43,zz),(f+.033,.43,zz)],.018,'gris')
        for s in [-1,1]:
            faro(t,[(s*.46,1.21),(s*.85,1.23),(s*.84,1.07),(s*.53,1.03)],f+.027)
            for y in [.61,.75]:
                ovalo(t,'Proyector óptico',f+.044,s*y,1.135,.050,.044,'cromo',.006)
            faro(t,[(s*.68,.86),(s*.82,.87),(s*.81,.73),(s*.68,.73)],f+.024,'Antiniebla Hilux')
    else:
        alto=.20 if estilo in ['ford_clasico','toyota_clasico'] else .14
        perfil=[(-.48,h+alto/2),(.48,h+alto/2),(.48,h-alto/2),(-.48,h-alto/2)]
        cara(t,'Parrilla principal rectangular',perfil,f+.022,'oscuro')
        contorno(t,'Contorno parrilla clásica',perfil,f+.032,.015,'cromo' if estilo=='toyota_clasico' else 'gris')
        for i in range(3):
            zz=h-alto*.33+i*alto*.33
            t.tubo('Lama parrilla clásica',[(f+.042,-.45,zz),(f+.042,.45,zz)],.008,'cromo' if estilo=='toyota_clasico' else 'gris')
        for s in [-1,1]:
            faro(t,[(s*.50,h+alto/2),(s*.79,h+alto/2),(s*.80,h-alto/2),(s*.50,h-alto/2)],f+.025)
            cara(t,'Intermitente exterior',[(s*.79,h+alto/2),(s*.85,h+alto/2-.01),(s*.85,h-alto/2),(s*.79,h-alto/2)],f+.036,'ambar')
            if estilo=='ford_clasico':
                t.cilindro('Hueco antiniebla',(f+.112,s*.63,z+.01),.081,.018,'oscuro','X',32,'decoracion')
                t.cilindro('Fondo antiniebla',(f+.124,s*.63,z+.01),.055,.01,'gris','X',32,'decoracion')
            else:
                t.caja('Intermitente parachoques',(f+.121,s*.64,z+.018),(.015,.18,.065),'ambar',.012,'decoracion')
    logo_z = {'dynamic_shield':1.08,'hilux':1.09,'ecosport':1.16}.get(estilo,h)
    emblema(t,f+.06,logo_z)
    t.caja('Soporte matrícula delantera',(f+.124,0,z-.008),(.022,.34,.16),'oscuro',.018,'decoracion')
    t.caja('Matrícula delantera',(f+.139,0,z-.008),(.008,.31,.135),'matricula',.009,'decoracion')
    if d.get('defensa'):
        for s in [-1,1]:
            t.tubo('Defensa tubular Hilux',[(f+.18,s*.57,.54),(f+.25,s*.58,.79),(f+.22,s*.49,1.23),(f+.14,s*.40,1.30)],.048,'oscuro')
        for zz in [.65,.94,1.30]:
            t.tubo('Travesaño defensa',[(f+.22,-.49,zz),(f+.22,.49,zz)],.042,'oscuro')


def trasera(t):
    d=t.d
    f=d['secciones'][0][0]-.014
    w=d['ancho']/2
    z=d['bajo']+.13
    mat={'gris':'gris','cromo':'cromo','pintura':'oscuro','oscuro':'oscuro'}[d['parachoques']]
    t.caja('Parachoques trasero',(f,0,z),(.22,w*1.92,.20),mat,.065)
    t.caja('Soporte matrícula trasera',(f-.119,0,z+.045),(.018,.35,.17),'oscuro',.018,'decoracion')
    t.caja('Matrícula trasera',(f-.133,0,z+.045),(.008,.31,.13),'matricula',.01,'decoracion')
    ancho=t.ancho(d['secciones'][0][0])*.94-.065
    for s in [-1,1]:
        if d['pilotos']=='montero':
            base,techo=d['luneta']
            def rx(z):
                if z<=d['secciones'][0][2]:return f-.018
                if z<base[1]:
                    u=(z-d['secciones'][0][2])/(base[1]-d['secciones'][0][2])
                    return f*(1-u)+base[0]*u-.018
                u=min(1,(z-base[1])/(techo[1]-base[1]))
                return base[0]*(1-u)+techo[0]*u-.018
            yz=[(s*(ancho+.11),1.51),(s*(ancho+.145),1.35),(s*(ancho+.055),1.19),(s*(ancho+.055),.76)]
            puntos=[(rx(z),y,z) for y,z in yz]
            t.tubo('Caja piloto vertical Montero',puntos,.045,'oscuro')
            t.tubo('Lente piloto vertical Montero',[(x-.010,y,z) for x,y,z in puntos],.032,'rojo')
            t.caja('Lente reversa Montero',(rx(1.14)-.017,s*(ancho+.01),1.14),(.013,.055,.065),'faro',.012,'decoracion')
        elif d['pilotos']=='ecosport':
            perfil=[(s*(ancho-.27),1.13),(s*(ancho+.015),1.18),(s*(ancho+.01),1.04),(s*(ancho-.20),.99)]
            cara(t,'Piloto trasero EcoSport',perfil,f-.018,'rojo')
            t.caja('Segmento reversa EcoSport',(f-.047,s*(ancho-.10),1.085),(.014,.12,.043),'faro',.012,'decoracion')
        else:
            zbase=d['cintura']-.31
            t.caja('Caja piloto trasero',(f-.018,s*ancho,zbase),(.05,.16,.40),'oscuro',.026,'decoracion')
            for dz,alto,matl in [(.13,.12,'ambar'),(.0,.14,'rojo'),(-.125,.09,'faro')]:
                t.caja('Segmento piloto '+matl,(f-.05,s*ancho,zbase+dz),(.014,.125,alto),matl,.016,'decoracion')
        t.caja('Reflector posterior',(f-.12,s*.59,z-.025),(.012,.12,.04),'rojo',.009,'decoracion')
    # Juntas y manija del portón, no una puerta superpuesta al volumen.
    for s in [-1,1]:
        t.tubo('Junta portón',[(f-.009,s*(w-.19),d['bajo']+.26),(f-.009,s*(w-.19),d['cintura']-.05)],.0035,'oscuro')
    t.caja('Tirador portón',(f-.035,0,d['cintura']-.15),(.035,.24,.06),'oscuro',.02,'decoracion')
    emblema(t,f-.055,d['cintura']-.29,True)
    if d['tipo']!='pickup':
        r=d['luneta'][0]
        t.tubo('Limpiaparabrisas trasero',[(r[0]-.028,-.08,r[1]+.07),(r[0]-.028,.39,r[1]+.075)],.009,'oscuro')
    t.caja('Escape',(f+.12,-.40,d['bajo']-.05),(.23,.07,.07),'gris',.025,'interior')


def accesorios(t):
    d=t.d
    for s in [-1,1]:
        if d['estribos']:
            a,b=d['ejes'][0]+.51,d['ejes'][1]-.51
            t.caja('Estribo lateral',((a+b)/2,s*(d['ancho']/2+.035),d['bajo']-.02),(b-a,.18,.075),'gris',.035,'decoracion')
            t.caja('Goma antideslizante',((a+b)/2,s*(d['ancho']/2+.035),d['bajo']+.023),(b-a-.09,.14,.012),'oscuro',.008,'decoracion')
        if d['id'] in ['vagoneta_blanca','ford_azul','ecosport_blanca']:
            # Moldura por tramo: se corta donde hay arco, nunca cruza la rueda.
            z=d['bajo']+.19
            tramos=[]
            actual=[]
            a,b=d['secciones'][0][0]+.1,d['secciones'][-1][0]-.1
            for i in range(201):
                x=a+(b-a)*i/200
                if all((x-e)**2+(z-d['radio_rueda'])**2>(d['radio_rueda']+.075)**2 for e in d['ejes']):
                    actual.append((x,t.chapa_y(x,z,s,.008),z))
                else:
                    if len(actual)>1: tramos.append(actual)
                    actual=[]
            if len(actual)>1: tramos.append(actual)
            for puntos in tramos:
                t.tubo('Moldura lateral recortada',puntos,.014,'gris' if d['id']=='ford_azul' else 'oscuro')
        if d.get('franjas'):
            perfiles=[ [(-2.32,1.16),(-.57,.91),(.75,1.07),(-.50,1.04)],
                       [(-2.30,1.08),(-.28,1.10),(.85,.88),(.53,1.00)] ]
            for p in perfiles:
                t.panel('Franja diagonal gris',[(x,t.chapa_y(x,z,s,.006),z) for x,z in p],'gris','decoracion')
        if d.get('rollbar'):
            x=d['caja_hasta']-.12
            t.tubo('Pata rollbar',[(x-.43,s*.75,1.29),(x,s*.73,1.81),(x+.13,s*.70,1.81)],.043,'oscuro')
    if d.get('rollbar'):
        x=d['caja_hasta']-.12
        t.tubo('Travesaño rollbar',[(x,-.73,1.81),(x,.73,1.81)],.043,'oscuro')
    # Costuras del capó en la superficie curva de los hombros.
    a,b=d['parabrisas'][0][0]+.04,d['secciones'][-1][0]-.16
    for s in [-1,1]:
        t.tubo('Junta capó',[(a+(b-a)*i/20,s*t.ancho(a+(b-a)*i/20)*.72,t.cintura(a+(b-a)*i/20)+.022) for i in range(21)],.003,'oscuro')
