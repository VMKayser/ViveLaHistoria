"""M061, R0088–R0095. Secuencia documentada en INVENTARIO_M061_DALENCE.md.
Frente ampliado hasta Dalence, recortado antes de colocar cada fachada.
"""
import math
from mathutils import Vector
from kit import *
from piezas_codex import prisma_seguro,recorte_estricto,trasladar,ventana_rebajada,copa_fina
from casas_codex import _cortar,cubierta_baja
from dalence_codex import decorar
from frentes_codex import frente_real,roseta
from varillas_codex import rama
A=(-313.954,-344.044);U=(.7394617427179232,-.6731985821855033);N=(-.6731985821855033,-.7394617427179232)
BLANCO='#eeeae3';GRIS='#788780';PIEDRA='#ac8965';HIERRO='#303a37';MADERA='#63372b'


def huella_conjunto(e):
    # El lienzo omite el frente de la UCB: se une a su cuerpo posterior,
    # respetando la medianera con E00e8b2 y recortando Dalence/Nicolás Ortiz.
    calle=next(c for c in datos.calles_reales() if 'Dalence' in c['nombre'] and c['eje'][0][0]<-250)
    eje=calle['eje'];w=calle['ancho']/2+.055
    def cruce(p,u,q,v):
        den=u[0]*v[1]-u[1]*v[0]
        if abs(den)<1e-5:return p
        t=((q[0]-p[0])*v[1]-(q[1]-p[1])*v[0])/den
        return (p[0]+t*u[0],p[1]+t*u[1])
    segmentos=[]
    for a,b in zip(eje,eje[1:]):
        L=math.dist(a,b);u=((b[0]-a[0])/L,(b[1]-a[1])/L)
        segmentos.append(((a[0]+u[1]*w,a[1]-u[0]*w),u))
    frente=[cruce(*segmentos[j-1],*segmentos[j]) for j in range(2,17)]
    # Las tangentes de la curva NO se prolongan a toda la cuadra:
    # la línea desplazada conserva cada quiebre real.
    h=[(-223.35,-346.24),(-261.75,-391.57)]+frente+[(-300.431,-328.266),(-289.82,-315.87),(-286.02,-311.43),(-277.74,-301.75)]
    v=(-300.431-A[0],-328.266-A[1]);normal=(v[1],-v[0])
    return _cortar(h,A,normal,0,1)


def huella_posterior(e):
    return _cortar(huella_conjunto(e),A,N,-15,-1)


def huella_tramo(e,t0,t1):
    h=huella_conjunto(e)
    h=_cortar(h,A,U,t0,1);h=_cortar(h,A,U,t1,-1)
    return recorte_estricto(_cortar(h,A,N,-15,1))


def cota_esquina(e):
    h=huella_tramo(e,58,90);f,g=frente_real({'huella':h},None,normal=N)
    p=f.punto(f.largo/2,0)
    return altura_suelo(p.x,p.y)


def cuerpo_tramo(e,nombre,t0,t1,alto,col,funcion):
    h=huella_tramo(e,t0,t1);c=Constructor(nombre+'_detalles');masa=Constructor(nombre)
    c.huella=h;masa.huella=h
    f,g=frente_real({'id':nombre,'huella':h},c,normal=N)
    # Datum de la calle, no del fondo alto de la manzana.
    p=f.punto(f.largo/2,0);z=altura_suelo(p.x,p.y)
    from volumenes_codex import cuerpo_escalonado
    cuerpo_escalonado(masa,[(h,z+alto)],min(altura_suelo(*p) for p in h)-.4,BLANCO)
    masa.objeto(col)
    decorar(c,h,z,N,funcion)
    c.objeto(col)
    return h,z


def ventana_aula(f,s,h,ancho=1.05,alto=2.05,abierta=False,reja=False):
    r=ancho/2;d=.025
    f.caja(s-r-.075,s+r+.075,h-.07,h+alto+.07,.005,.04,'marco_ventana',GRIS)
    f.caja(s-r+.03,s+r-.03,h+.025,h+alto-.035,.041,.045,'vidrio','#64746e' if abierta else '#92a099')
    for ss in (s-r,s,s+r):f.caja(ss-.022,ss+.022,h,h+alto,d,.095,'marco_ventana',GRIS)
    for hh in (h,h+.35,h+alto-.32,h+alto):f.caja(s-r,s+r,hh-.022,hh+.022,d,.10,'marco_ventana',GRIS)
    if not abierta:
        for j in range(7):
            hh=h+.47+j*(alto-.9)/7
            f.caja(s-r+.04,s+r-.04,hh,hh+.04,.047,.067,'marco_ventana','#7b8981')
    else:
        # Hoja basculante físicamente conectada al travesaño superior.
        for x0,x1 in ((s-r,s),(s,s+r)):
            f.c.poligono([f.punto(x0,h+alto-.32,.09),f.punto(x1,h+alto-.32,.09),
                f.punto(x1,h+alto-.72,.31),f.punto(x0,h+alto-.72,.31)],'vidrio','#83938b')
    if reja:
        for j in range(5):f.caja(s-r+.10+j*(ancho-.2)/4-.012,s-r+.10+j*(ancho-.2)/4+.012,h-.12,h+alto+.12,.11,.135,'hierro',HIERRO)
        for hh in (h-.05,h+.65,h+alto+.05):f.caja(s-r-.08,s+r+.08,hh,hh+.025,.11,.14,'hierro',HIERRO)


# Trazos propios: ningún archivo de fuente ni recurso ajeno.
LETRAS={
 'A': [[(0,0),(.3,1),(.6,0)],[(.12,.4),(.48,.4)]],
 'B': [[(0,0),(0,1),(.45,1),(.6,.8),(.45,.5),(0,.5)],[(.45,.5),(.6,.2),(.45,0),(0,0)]],
 'C': [[(.6,1),(.1,1),(0,.8),(0,.2),(.1,0),(.6,0)]],
 'D': [[(0,0),(0,1),(.4,1),(.6,.8),(.6,.2),(.4,0),(0,0)]],
 'E': [[(.6,1),(0,1),(0,0),(.6,0)],[(0,.5),(.45,.5)]],
 'I': [[(0,1),(.5,1)],[(.25,1),(.25,0)],[(0,0),(.5,0)]],
 'L': [[(0,1),(0,0),(.6,0)]],
 'N': [[(0,0),(0,1),(.6,0),(.6,1)]],
 'O': [[(.1,0),(0,.2),(0,.8),(.1,1),(.5,1),(.6,.8),(.6,.2),(.5,0),(.1,0)]],
 'R': [[(0,0),(0,1),(.45,1),(.6,.8),(.45,.55),(0,.55)],[(.25,.55),(.6,0)]],
 'S': [[(.6,1),(0,1),(0,.55),(.6,.45),(.6,0),(0,0)]],
 'T': [[(0,1),(.6,1)],[(.3,1),(.3,0)]],
 'U': [[(0,1),(0,.1),(.15,0),(.45,0),(.6,.1),(.6,1)]],
 'V': [[(0,1),(.3,0),(.6,1)]]}


def letras_institucion(f,texto,s,h,alto):
    inicio=s-(len(texto)*.8-.2)*alto/2
    for i,letra in enumerate(texto):
        for trazo in LETRAS[letra]:
            for a,b in zip(trazo,trazo[1:]):
                rama(f.c,f.punto(inicio+(i*.8+a[0])*alto,h+a[1]*alto,.025),
                     f.punto(inicio+(i*.8+b[0])*alto,h+b[1]*alto,.025),
                     alto*.05,alto*.05,'letrero','#ad9874')


def patio_cerrado(e,col):
    h=huella_tramo(e,0,10)
    piso=Constructor('M061_UCB_atrio_piso')
    piso.poligono([(x,y,altura_suelo(x,y)+.08) for x,y in h],'adoquin','#b8b1a1');piso.objeto(col,huella=h)
    c=Constructor('M061_UCB_cerramiento');f,g=frente_real({'huella':h},c,normal=N)
    p=f.punto(f.largo/2,0);z=altura_suelo(p.x,p.y)
    def muro(f):
        f.caja(0,f.largo,-.6,4.8,-.25,0,'muro',BLANCO)
        zocalo(f,2.65,desde=-.6,color=PIEDRA)
        cornisa(f,4.75,alto=.12,vuelo=.12,color=BLANCO)
    decorar(c,h,z,N,muro);c.objeto(col,huella=h)
    # El pabellón vive dentro del patio y de su medianera oblicua.
    # La antigua caja rectangular salía del lote por su esquina izquierda.
    ph=h
    for a,n,lim,signo in ((tuple(f.a[:2]),tuple(f.n[:2]),-3.05,-1),
                         (tuple(f.a[:2]),tuple(f.n[:2]),-6,1),
                         (tuple(f.a[:2]),tuple(f.u[:2]),.35,1),
                         (tuple(f.a[:2]),tuple(f.u[:2]),f.largo-.35,-1)):
        ph=_cortar(ph,a,n,lim,signo)
    assert len(ph)>2,'Pabellón sin huella propia'
    c=Constructor('M061_UCB_pabellon')
    c.prisma(ph,min(altura_suelo(*p) for p in ph)-.4,z+4.8,'muro',BLANCO,tapa=False,piso=True)
    c.prisma(ph,z+4.8,z+7.5,'vidrio','#35434a',tapa=True)
    c.objeto(col,huella=ph)
    c=Constructor('M061_UCB_pabellon_detalles')
    def ventanales(f):
        for j in range(7):
            ss=.1+(f.largo-.2)*j/6
            f.caja(ss-.025,ss+.025,4.8,7.5,.005,.055,'metal',HIERRO)
        for hh in (5.0,5.8,6.6,7.5):f.caja(.05,f.largo-.05,hh-.018,hh+.018,.005,.055,'metal',HIERRO)
        for ss in (f.largo*.36,f.largo*.64):
            f.c.poligono([f.punto(ss-.40,6.55,.06),f.punto(ss+.40,6.55,.06),f.punto(ss+.40,6.06,.34),f.punto(ss-.40,6.06,.34)],'vidrio','#95a39c')
    decorar(c,ph,z,N,ventanales);c.objeto(col)


def pilon_piedra(e,col):
    def frente(f):
        zocalo(f,14.0,desde=-.8,color=PIEDRA,rol='piedra')
        cornisa(f,14.0,alto=.12,vuelo=.10,rol='piedra',color='#c1ab8a')
        s=f.largo/2;h=11.1;r=min(1.4,f.largo*.38)
        # Monograma P dentro de círculo, asta, travesaño y rayos.
        f.arco(s,r,.055,h,.085,.15,'hierro',HIERRO,medio=False,segmentos=40)
        f.caja(s-.08,s+.08,6.3,h+r*.8,.06,.17,'hierro',HIERRO)
        f.caja(s-r-.30,s+r+.30,h-.55,h-.41,.06,.17,'hierro',HIERRO)
        f.caja(s-.05,s+.30,h+.65,h+.79,.06,.17,'hierro',HIERRO)
        f.caja(s-.05,s+.30,h+.08,h+.22,.06,.17,'hierro',HIERRO)
        for k in range(12):
            a=math.pi/2-k*math.pi/12;b=a-math.pi/12
            rama(f.c,f.punto(s+.28+.45*math.cos(a),h+.45+.30*math.sin(a),.115),
                 f.punto(s+.28+.45*math.cos(b),h+.45+.30*math.sin(b),.115),.055,.055,'hierro',HIERRO)
        for ds in (-1.25,-.65,.65,1.25):rama(f.c,f.punto(s+ds,h-3.4,.1),f.punto(s+ds*.3,h-.55,.1),.026,.026,'hierro',HIERRO)
    cuerpo_tramo(e,'M061_pilon_UCB',10,15,14.05,col,frente)


def bloque_moderno(e,col):
    def frente(f):
        zocalo(f,2.8,desde=-.8,color=PIEDRA)
        for j in range(5):
            ss=(j+.5)*f.largo/5
            for k,hh in enumerate((3.8,7.15,10.50)):ventana_aula(f,ss,hh,ancho=1.35,alto=1.48,abierta=j==4)
            ventana_aula(f,ss,1.2,ancho=1.05,alto=1.5,reja=True)
        for hh in (2.8,6.1,9.45,12.9):cornisa(f,hh,alto=.16,vuelo=.22,color=BLANCO)
        parapeto(f,13.05,alto=.8,color=BLANCO)
    h,z=cuerpo_tramo(e,'M061_UCB_moderno',15,27,13.9,col,frente)
    # Retorno occidental documentado a través del patio.
    c=Constructor('M061_UCB_moderno_detalles_retorno');ls=lados(h)
    l=min(ls,key=lambda l:abs(l['normal'][0]*U[0]+l['normal'][1]*U[1]+1))
    f=Fachada(c,l,z)
    zocalo(f,2.8,desde=-.8,color=PIEDRA)
    for hh in (3.8,7.15,10.5):
        for j in range(4):ventana_aula(f,(j+.5)*f.largo/4,hh,ancho=1.3,alto=1.5)
    for hh in (2.8,6.1,9.45,13.0):cornisa(f,hh,alto=.16,vuelo=.14,color=BLANCO)
    c.objeto(col)


def aulas(e,col):
    def frente(f):
        zocalo(f,2.8,desde=-.8,color=PIEDRA)
        paso=f.largo/7
        for j in range(7):
            centro=(j+.5)*paso
            for hh in (3.7,7.05,10.35):
                if j==6 and hh==3.7:continue  # Panel institucional, no dos ventanas.
                for signo in (-1,1):ventana_aula(f,centro+signo*.73,hh,ancho=1.10,alto=2.05,abierta=(j==6 and signo==-1 and hh>10))
            if j<6:
                ventana_aula(f,centro,1.1,ancho=1.35,alto=1.45,reja=True)
            for hh in (6.7,10.0):
                f.caja(j*paso+.06,j*paso+.14,hh,hh+3.05,.005,.035,'moldura',BLANCO)
            if j in (1,3,5):
                for hh in (6.5,9.8,13):
                    ss=j*paso+.28
                    f.caja(ss-.10,ss+.10,hh-.26,hh-.06,.04,.06,'hierro','#727b73')
                    for k in range(4):f.caja(ss-.09,ss+.09,hh-.24+k*.04,hh-.225+k*.04,.061,.075,'moldura',BLANCO)
        # Acceso final, no un vano de aula en el basamento.
        ss=f.largo-paso*.48
        puerta(trasladar(f,h=.08,d=.075),ss,ancho=3.1,alto=3.25,color=MADERA,color_moldura=BLANCO)
        for a in (-1.12,-.38,.38,1.12):
            for hh in (.3,.9,1.5,2.1,2.7):
                f.caja(ss+a-.28,ss+a+.28,hh,hh+.45,.13,.165,'madera','#754537')
        f.caja(ss-1.82,ss+1.82,3.32,3.48,-.05,.58,'moldura',BLANCO)
        # Placa verde del punto de encuentro, junto a la jamba derecha.
        sp=ss+1.84
        f.caja(sp-.22,sp+.22,2.66,3.31,.03,.08,'letrero','#305e47')
        for signo in (-1,1):
            for vertical in (-1,1):
                x=sp+signo*.13;y=3.04+vertical*.13
                rama(f.c,f.punto(x,y,.085),f.punto(sp+signo*.045,3.04+vertical*.045,.085),.009,.009,'letrero','#eeeae3')
                f.c.poligono([f.punto(sp+signo*.025,3.04+vertical*.025,.085),f.punto(sp+signo*.08,3.04+vertical*.027,.085),f.punto(sp+signo*.027,3.04+vertical*.08,.085)],'letrero','#eeeae3')
        for hh in (2.76,2.81):f.caja(sp-.14,sp+.14,hh,hh+.018,.081,.087,'letrero','#eeeae3')
        # Escudo y rótulo institucional, trazos propios sin fuente externa.
        f.arco(ss-.88,.34,.025,4.35,.025,.07,'letrero','#b9a47b',medio=False,segmentos=28)
        for signo in (-1,1):rama(f.c,f.punto(ss-.88+signo*.18,4.15,.07),f.punto(ss-.88-signo*.15,4.50,.07),.014,.014,'letrero','#b9a47b')
        for texto,hh,alto in (('UNIVERSIDAD',4.60,.13),('CATOLICA',4.35,.20),('BOLIVIANA',4.12,.16)):
            letras_institucion(f,texto,ss+.48,hh,alto)
        for hh in (2.8,6.35,9.65):cornisa(f,hh,alto=.20,vuelo=.25,color=BLANCO)
        cornisa(f,13.0,alto=.20,vuelo=.25,color=BLANCO)
        alero_tejas(f,13.22,vuelo=.30,fondo=3,canes=True)
    cuerpo_tramo(e,'M061_UCB_aulas',27,58,13.25,col,frente)


def esquina(e,col):
    def frente(f):
        L=f.largo
        zocalo(f,1.35,desde=-.8,color='#b39878')
        for hh in [1.5+j*.39 for j in range(18)]:f.caja(0,L,hh,hh+.018,.001,.018,'moldura','#c3c4b7')
        # PB ciega con paneles de antiguas aberturas, tal como R0094/95.
        for ss in (L*.27,L*.76):
            for a,b,x,y in ((ss-.72,ss-.64,1.55,3.9),(ss+.64,ss+.72,1.55,3.9),(ss-.72,ss+.72,3.82,3.9)):
                f.caja(a,b,x,y,.02,.07,'moldura','#f3efe5')
            f.caja(ss-.64,ss+.64,1.55,3.82,.02,.025,'muro','#e4e2d8')
        ss=L*.76
        ventana_rebajada(f,ss,5.05,ancho=1.4,alto=2.2,color_moldura=BLANCO,color_carpinteria=MADERA,panel=True)
        for j in range(12):
            a=j*math.pi/12;b=(j+1)*math.pi/12
            f.c.poligono([f.punto(ss+.96*math.cos(a),7.52+.22*math.sin(a),.06),f.punto(ss+.96*math.cos(b),7.52+.22*math.sin(b),.06),f.punto(ss+.96*math.cos(b),7.61+.22*math.sin(b),.06),f.punto(ss+.96*math.cos(a),7.61+.22*math.sin(a),.06)],'moldura','#d2cbbb',grosor=.08,normal_extrusion=-f.n)
        for s in (.14,L*.50,L-.14):
            pilastra(f,s,1.35,8.7,ancho=.38,vuelo=.10,color=BLANCO)
            for h in (4.35,8.5):
                f.caja(s-.3,s+.3,h,h+.15,.03,.20,'moldura',BLANCO)
                for signo in (-1,1):f.arco(s+signo*.15,.075,.025,h-.05,.07,.14,'moldura',BLANCO,medio=False,segmentos=8)
        for hh in (4.4,8.6):cornisa(f,hh,alto=.27,vuelo=.26,color=BLANCO)
        parapeto(f,8.9,alto=.4,color=BLANCO)
    cuerpo_tramo(e,'M061_esquina_UCB',58,90,9.3,col,frente)


def hojas_ralas(c,q,u,n,semilla):
    """Hojas compuestas y ramitas colgantes; evita racimos esféricos densos."""
    import random
    az=random.Random(semilla)
    for j in range(4):
        centro=q+u*az.uniform(-.30,.30)+n*az.uniform(-.16,.16)+Vector((0,0,az.uniform(-.20,.20)))
        fin=centro+u*.22+Vector((0,0,-.45))
        rama(c,q,centro,.006,.004,'tronco','#746049')
        rama(c,centro,fin,.005,.002,'tronco','#746049')
        for k in range(6):
            base=centro.lerp(fin,(k+.3)/6)
            for signo in (-1,1):
                punta=base+n*(signo*(.16-k*.013))+u*.065+Vector((0,0,-.18))
                lado=u*.040
                c.poligono([base-lado,base+lado,punta], 'follaje',
                           ('#5c763c','#748842','#87904b','#9a8150')[(k+j+semilla)%4])


def arboles(e,col):
    # Copas ralas documentadas, cada ramita conectada al ramaje principal.
    for j,t in enumerate((7.0,14.0,24.5,35.0,45.0,53.0,62.5)):
        h=huella_tramo(e,max(0,t-1),t+1);f,g=frente_real({'huella':h},None,normal=N)
        p=f.punto(f.largo*.5,0,.95);z=altura_suelo(p.x,p.y);c=Constructor(f'M061_UCB_arbol_{j}')
        grande=j in (0,1,6);H=6.8 if grande else 3.3
        if not grande:
            c.caja(p.x-.32,p.y-.32,z-.08,p.x+.32,p.y+.32,z+.5,'piedra','#bcbdb1')
        tronco=Vector((p.x,p.y,z-.08));cima=Vector((p.x+.15,p.y,z+H*.46))
        rama(c,tronco,cima,.09,.045,'tronco','#69503c')
        for k in range(9):
            ang=k*2.39996;r=(1.9 if grande else .50)+(k%3)*.18
            q=cima+f.u*(r*math.cos(ang))+f.n*(.38*math.sin(ang))+Vector((0,0,H*.35+.55*math.sin(ang*1.7)))
            rama(c,cima-Vector((0,0,k*.035)),q,.027,.009,'tronco','#69503c')
            hojas_ralas(c,q,f.u,f.n,880+j*20+k)
        c.objeto(col)


def farol_dalence(e,col):
    """Poste delgado y brazo curvo que aparece delante de las aulas en R0091."""
    f,_=frente_real({'huella':huella_tramo(e,36.5,37.5)},None,normal=N)
    p=f.punto(f.largo*.5,0,1.22);p.z=altura_suelo(p.x,p.y)
    c=Constructor('M061_UCB_postes_farol_Dalence')
    c.cilindro(p.x,p.y,p.z-.18,p.z+.20,.085,'metal','#717c74',lados=8)
    c.cilindro(p.x,p.y,p.z,p.z+8.20,.045,'metal','#89958d',lados=8,radio_arriba=.032)
    puntos=[p+Vector((0,0,8.0)),p+f.n*.12+Vector((0,0,8.48)),
            p+f.n*.52+Vector((0,0,8.66)),p+f.n*.85+Vector((0,0,8.45))]
    for a,b in zip(puntos,puntos[1:]):rama(c,a,b,.026,.026,'metal','#58675e')
    q=puntos[-1]
    c.cilindro(q.x,q.y,q.z-.11,q.z+.035,.17,'metal','#3d4b42',lados=8,radio_arriba=.065)
    c.esfera(q.x,q.y,q.z-.10,.10,'vidrio','#c2c8b4',segmentos=8)
    c.objeto(col)


def construir_frente(e,col):
    patio_cerrado(e,col);pilon_piedra(e,col);bloque_moderno(e,col);aulas(e,col);esquina(e,col);arboles(e,col);farol_dalence(e,col)


def tendidos(e,col):
    """Haz de seis conductores de las fotos, en ménsulas y aisladores reales."""
    from piezas_codex import cable_curvo
    from detalles_plaza_codex import punto_encadenado
    from tendidos_codex import bvh_coleccion
    from dalence_codex import anclajes_poste
    f,g=frente_real({'huella':huella_conjunto(e)},None,0,normal=N)
    s=0;estaciones=[13.0]
    for l in g['lados']:
        s+=l['largo']
        if 13.1<s<g['largo']-.8:estaciones.append(s)
    estaciones.append(g['largo']-.8)
    obstaculos=bvh_coleccion(col);c=Constructor('M061_UCB_cables')
    apoyos=[]
    for i,ss in enumerate(estaciones):
        p=punto_encadenado(g,ss,0,0);q=punto_encadenado(g,ss,0,.40)
        n=(q-p).normalized();z=altura_suelo(p.x,p.y)
        puntos=[]
        for k in range(6):
            h=7.55+k*.08
            a=Vector((p.x,p.y,z+h));b=Vector((q.x,q.y,z+h))
            rama(c,a-n*.025,b,.025,.025,'hierro',HIERRO)
            c.esfera(*b,.042,'vidrio','#8fa59c',segmentos=6)
            puntos.append(b)
        apoyos.append(puntos)
    def libre(a,b,flecha):
        puntos=[]
        for j in range(25):
            t=j/24;q=a.lerp(b,t);q.z-=4*flecha*t*(1-t);puntos.append(q)
        for p,q in zip(puntos[1:-2],puntos[2:-1]):
            delta=q-p
            if obstaculos.ray_cast(p,delta.normalized(),delta.length)[0] is not None:return False
        return True
    for ap,bp in zip(apoyos,apoyos[1:]):
        for a,b in zip(ap,bp):
            flecha=min(.08,(b-a).length*.006)
            assert libre(a,b,flecha),'Conductor atraviesa arquitectura'
            cable_curvo(c,a,b,flecha=flecha,radio=.009,segmentos=12)
    # Los conductores continúan desde el poste de E00 cuando el vano está libre.
    salidas=anclajes_poste('M061')[3];conectados=0
    for a,b in zip(salidas,apoyos[0]):
        if libre(a,b,.13):
            cable_curvo(c,a,b,flecha=.13,radio=.009,segmentos=24);conectados+=1
    c.objeto(col)
    print('[UCB] Seis conductores sujetos a ménsulas; conexiones al poste:',conectados,flush=True)
