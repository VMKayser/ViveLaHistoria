"""M061 — Nicolás Ortiz: Universidad, paño blanco y frente del museo.

Hoja completa de 11 fotos examinada. E311863 lado 8, s=20..59 m:
130923–130946, muro de cal blanca #eeeae5, zócalo arenisca .6 m,
cuatro ventanas altas enmarcadas, guardapolvos curvos, remates piramidales,
placas y macetas colgadas. No confundir este paño con la Catedral de enfrente.
E311863 s=0..20: frente neoclásico de dos plantas de la Universidad,
130946–131002, ventanas de madera rojiza, arcos rebajados en las altas,
pilastras, enlucido horizontal y cornisa recta. Puerta en s~18 del primer tramo.
E00e8b2: mansarda y nueve ranuras, R0085/86 y R0088/89.
E1e60e8 (Archivo): sin foto propia, versión colonial sencilla.
Dalence de E311863: ampliación documentada R0089–R0095 en ucb_dalence.py;
patio/pilón, campus de cuatro niveles y esquina de dos plantas.
Inventario previo en INVENTARIO_M061_DALENCE.md.
Alturas estimadas y repartos contrastados con las vistas de calle.
E02ae75: frente del Museo Eclesiástico (130907–130923), cinco ejes;
las fotos de la Universidad asociadas por cercanía corresponden al extremo
de Dalence de E311863. El POI del museo queda detrás, en M063.
"""
import os
import sys
import math
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..'))
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from kit import *
from piezas_codex import prisma_seguro, trasladar, farol_pie, arbol_podado, ventana_rebajada, poste_vereda, cable_curvo, semaforo_esquina
from museo_codex import detallar_museo
from casas_codex import casa_minima
AGENTE='codex';MANZANA='M061';BLANCO='#eeeae5';PIEDRA='#b59978'
m,col=iniciar(AGENTE,MANZANA)


def cuerpo(e,alto):
    c=Constructor(e['id']+'_detalles');masa=Constructor(e['id']);ls=lados(e['huella'])
    z=max(altura_suelo(*p) for p in e['huella']);zb=min(altura_suelo(*p) for p in e['huella'])-.5
    h=e['huella']
    if e['id']=='E311863':
        from ucb_dalence import huella_posterior,cota_esquina
        from casas_codex import _cortar
        h=huella_posterior(e);l=ls[8]
        u=((l['b'][0]-l['a'][0])/l['largo'],(l['b'][1]-l['a'][1])/l['largo'])
        esquina_h=_cortar(h,l['a'],u,20,-1);resto_h=_cortar(h,l['a'],u,20,1)
        from volumenes_codex import cuerpo_escalonado
        tramos=[(p,H) for p,H in ((esquina_h,cota_esquina(e)+8.9),(resto_h,z+alto)) if len(p)>2]
        cuerpo_escalonado(masa,tramos,zb,BLANCO)
    else:
        from volumenes_codex import cuerpo_escalonado
        cuerpo_escalonado(masa,[(h,z+alto)],zb,BLANCO)
    masa.objeto(col,huella=h);c.huella=h
    return c,ls,z,zb


def desague_saliente(f,s,h):
    """Caño blanco hueco con ménsula, fotografiado en 130929/130936."""
    radio=.095;interior=.065
    for k in range(6):
        a=k*math.tau/6;b=(k+1)*math.tau/6
        def p(ang,r,d):
            return f.punto(s+r*math.cos(ang),h+r*math.sin(ang)-.13*d,d)
        f.c.poligono([p(a,radio,.05),p(b,radio,.05),p(b,radio,.85),p(a,radio,.85)],'moldura',BLANCO)
        f.c.poligono([p(a,interior,.05),p(a,interior,.85),p(b,interior,.85),p(b,interior,.05)],'piedra','#78746b')
        f.c.poligono([p(a,radio,.85),p(b,radio,.85),p(b,interior,.85),p(a,interior,.85)],'moldura',BLANCO)
    f.caja(s-.13,s+.13,h-.24,h-.12,.02,.38,'moldura',BLANCO)


def banderola_ucb(f,s,nombre):
    """131002: banderolas azules DERECHO/MEDICINA, trazos propios de bajo coste."""
    from ucb_dalence import LETRAS
    glifos=dict(LETRAS)
    glifos['H']=[[(0,0),(0,1)],[(.6,0),(.6,1)],[(0,.5),(.6,.5)]]
    glifos['M']=[[(0,0),(0,1),(.3,.45),(.6,1),(.6,0)]]
    f.caja(s-.44,s+.44,2.70,4.78,.31,.33,'letrero','#292e49')
    f.caja(s-.53,s+.53,4.78,4.83,-.025,.37,'hierro','#3e423b')
    for j in range(12):
        a=j*math.tau/12;b=(j+1)*math.tau/12
        f.c.poligono([f.punto(s+.18*math.cos(a),4.28+.18*math.sin(a),.331),
                     f.punto(s+.18*math.cos(b),4.28+.18*math.sin(b),.331),
                     f.punto(s+.165*math.cos(b),4.28+.165*math.sin(b),.331),
                     f.punto(s+.165*math.cos(a),4.28+.165*math.sin(a),.331)],'letrero','#baad83')
    # Letras triangulares: legibles en el plano frontal sin cilindros ni fuentes.
    for texto,alto,h in (('UCB',.14,3.88),(nombre,.085,2.96)):
        inicio=s-(len(texto)*.8-.2)*alto/2
        for i,letra in enumerate(texto):
            for trazo in glifos[letra]:
                for a,b in zip(trazo,trazo[1:]):
                    x0=inicio+(i*.8+a[0])*alto;y0=h+a[1]*alto
                    x1=inicio+(i*.8+b[0])*alto;y1=h+b[1]*alto
                    dx,dy=x1-x0,y1-y0;L=math.hypot(dx,dy);w=alto*.045
                    if L<1e-6:continue
                    f.c.poligono([f.punto(x0-dy/L*w,y0+dx/L*w,.332),
                                 f.punto(x0+dy/L*w,y0-dx/L*w,.332),f.punto(x1,y1,.332)],'letrero','#c4b793')
    for h in (3.64,3.69):
        f.c.poligono([f.punto(s-.24,h,.332),f.punto(s+.24,h,.332),
                     f.punto(s+.24,h+.012,.332),f.punto(s-.24,h+.012,.332)],'letrero','#baad83')


def paño_clasico(f,zb,s0=0,s1=None,puerta_s=None):
    s1=f.largo if s1 is None else s1
    n=max(1,round((s1-s0)/4.4));paso=(s1-s0)/n
    for k in range(n):
        ss=s0+(k+.5)*paso
        es_puerta=puerta_s is not None and abs(ss-puerta_s)<paso/2
        if es_puerta:
            pie=f.punto(ss,0)
            fp=trasladar(f,h=altura_suelo(pie.x,pie.y)+.1-f.suelo)
            puerta(fp,ss,ancho=1.65,alto=3.0,color='#704433',color_moldura=PIEDRA)
        else:
            # 131002: balconera baja de madera, sin una reja inventada.
            f.caja(ss-.6,ss+.6,1.4,3.85,.005,.025,'vidrio','#b2b8af')
            f.caja(ss-.6,ss+.6,1.4,2.05,.026,.06,'madera','#673445')
            for dx in (-.6,0,.6):f.caja(ss+dx-.035,ss+dx+.035,1.4,3.85,.025,.085,'marco_ventana','#673445')
            for hh in (1.42,2.05,2.65,3.25,3.83):f.caja(ss-.6,ss+.6,hh,hh+.035,.03,.09,'marco_ventana','#673445')
            for dx in (-.74,.74):f.caja(ss+dx-.06,ss+dx+.06,1.32,3.95,.005,.08,'moldura',BLANCO)
            cornisa(f,3.93,s0=ss-.82,s1=ss+.82,alto=.10,vuelo=.14,color=BLANCO)
            zocalo(f,1.35,s0=s0+k*paso,s1=s0+(k+1)*paso,desde=zb-f.suelo,color=PIEDRA)
        ventana_rebajada(f,ss,5.0,ancho=1.3,alto=2.25,color_moldura=BLANCO,panel=True,color_carpinteria='#673445')
        # Arco rebajado sobre el dintel: guardapolvo de moldura.
        for j in range(8):
            a=math.pi*j/8;b=math.pi*(j+1)/8
            f.c.poligono([f.punto(ss+.85*math.cos(a),7.7+.22*math.sin(a),.14),
                           f.punto(ss+.85*math.cos(b),7.7+.22*math.sin(b),.14),
                           f.punto(ss+.85*math.cos(b),7.78+.22*math.sin(b),.14),
                           f.punto(ss+.85*math.cos(a),7.78+.22*math.sin(a),.14)],'moldura',BLANCO,grosor=.17,normal_extrusion=-f.n)
        for hh in (1.45,1.65,2.2,2.75,3.3,3.85,5.0,5.55,6.1,6.65,7.2,7.85):
            for a,b in ((ss-paso/2+.2,ss-.85),(ss+.85,ss+paso/2-.2)):
                if b>a:f.caja(a,b,hh,hh+.025,.015,.035,'moldura',BLANCO)
        if es_puerta:
            for a,b in ((ss-paso/2,ss-1.05),(ss+1.05,ss+paso/2)):
                zocalo(f,1.35,s0=a,s1=b,desde=zb-f.suelo,color=PIEDRA)
    for k in range(n+1):
        ss=s0+k*paso
        pilastra(f,ss,0,8.7,ancho=.4,vuelo=.10,color=BLANCO)
        for hh in (4.05,8.55):
            f.caja(ss-.28,ss+.28,hh-.08,hh+.10,.10,.20,'moldura',BLANCO)
            for ds in (-.17,.17):
                f.arco(ss+ds,.075,.03,hh,.17,.20,'moldura',BLANCO,medio=False,segmentos=5)
    for hh in (4.2,8.6):cornisa(f,hh,s0=s0,s1=s1,alto=.24,vuelo=.26,color=BLANCO)
    parapeto(f,8.9,alto=.4,s0=s0,s1=s1,color=BLANCO)

for e in m['edificios']:
    if e['id']=='E311863':
        c,ls,z,zb=cuerpo(e,8.9)
        f=Fachada(c,ls[8],z)
        from ucb_dalence import cota_esquina
        fc=trasladar(f,h=cota_esquina(e)-z)
        paño_clasico(fc,zb,s1=20,puerta_s=18)
        for ss,nombre in ((2.0,'DERECHO'),(6.0,'MEDICINA')):banderola_ucb(fc,ss,nombre)
        # 131002: cornisa recta; el frontón visible pertenece al edificio de enfrente.
        zocalo(f,.65,s0=20,desde=zb-z,color=PIEDRA)
        for ss in (25,35,45,55):
            if ss!=55:
                ventana_rebajada(f,ss,4.0,ancho=1.3,alto=2.45,reja=True,color_moldura=BLANCO)
            else:
                # El último vano está cerrado con bloques translúcidos (130923/130929).
                f.caja(ss-.65,ss+.65,4.0,6.23,0,.03,'vidrio','#a6a193')
                c.poligono([f.punto(ss-.65*math.cos(j*math.pi/16),6.23+.22*math.sin(j*math.pi/16),.032)
                            for j in range(17)],'vidrio','#a6a193')
                for j in range(10):
                    hh=4+j*.24
                    f.caja(ss-.65,ss+.65,hh,hh+.018,.034,.041,'moldura','#c0b9a9')
                for j in range(7):
                    dx=-.62+j*.205;hh=6.23+.22*math.sqrt(max(0,1-(dx/.65)**2))
                    f.caja(ss+dx,ss+dx+.018,4,hh,.034,.041,'moldura','#c0b9a9')
            # Gran marco con alféizar y guardapolvo de arco rebajado.
            for ds in (-1.0,1.0):pilastra(f,ss+ds,3.85,7.1,ancho=.17,vuelo=.16,color=BLANCO)
            cornisa(f,7.1,s0=ss-1.12,s1=ss+1.12,alto=.16,vuelo=.23,color=BLANCO)
            f.arco(ss,.8,.12,6.2,0,.15,'moldura',BLANCO,segmentos=12)
            f.caja(ss-.7,ss+.7,3.0,3.35,.04,.07,'letrero')
        cornisa(f,8.65,s0=20,alto=.25,vuelo=.22,color=BLANCO)
        for ss in (21,28,37,46,55,59):
            f.caja(ss-.22,ss+.22,8.9,9.12,-.3,.10,'moldura',BLANCO)
            p=f.punto(ss,9.12,-.1)
            c.cilindro(p.x,p.y,p.z,p.z+.35,.24,'moldura',BLANCO,lados=4,radio_arriba=.035)
        for ss in (22,31,40,49,58):desague_saliente(f,ss,8.1)
        # Macetas de pared, visibles a lo largo del paño blanco (130929/130936).
        for ss in (23,30,39,49,57):
            p=f.punto(ss,3.3,.22)
            c.cilindro(p.x,p.y,p.z,p.z+.27,.12,'teja',lados=8,radio_arriba=.20)
            c.esfera(p.x,p.y,p.z+.3,.17,'follaje',segmentos=8)
            for signo in (-1,1):
                for j in range(12):
                    a=j*math.tau/12;b=(j+1)*math.tau/12
                    centro=ss+signo*.23
                    c.poligono([f.punto(centro+.10*math.cos(a),3.25+.10*math.sin(a),.23),
                                f.punto(centro+.10*math.cos(b),3.25+.10*math.sin(b),.23),
                                f.punto(centro+.12*math.cos(b),3.25+.12*math.sin(b),.23),
                                f.punto(centro+.12*math.cos(a),3.25+.12*math.sin(a),.23)],'hierro')
        for ss in (22,31,40,49,58):
            f.caja(ss-.13,ss+.13,3.25,3.35,.02,.23,'hierro')
        c.objeto(col)
    elif e['id']=='E02ae75':
        c,ls,z,zb=cuerpo(e,8.4)
        detallar_museo(c,ls[5],z,zb)
        c.objeto(col)
    elif e['id']=='E00e8b2':
        from dalence_codex import edificio_moderno
        edificio_moderno(e,col)
    else:
        if e['id']=='E1e60e8':
            from dalence_huellas_codex import huella_pabellon_m060
            e=dict(e,excluir_huellas=[huella_pabellon_m060(margen=.14)])
        casa_minima(e,col)
from ucb_dalence import construir_frente
construir_frente(edificio(MANZANA,'E311863'),col)
# Árboles en macetas de vereda y faroles documentados; BASE no se altera.
e=edificio(MANZANA,'E311863');f=Fachada(None,lados(e['huella'])[8],0)
for k,ss in enumerate((8,19,31,43,55)):
    p=f.punto(ss,0,1.1);z=altura_suelo(p.x,p.y)
    maceta=Constructor(f'M061_maceta_{k}')
    maceta.caja(p.x-.35,p.y-.35,z,p.x+.35,p.y+.35,z+.65,'moldura',BLANCO)
    maceta.objeto(col)
    arbol_podado(f'M061_arbol_{k}',p.x,p.y,col,radio=.65,alto=2.6,direccion=tuple(f.n[:2]))
for k,ss in enumerate((15,38)):
    p=f.punto(ss,0,1.35);farol_pie(f'M061_postes_farol_{k}',p.x,p.y,col,alto=3.5)
# Línea del alumbrado de los proyectores, sujeta al propio paño (130929).
c=Constructor('M061_cables_proyectores')
f=Fachada(c,lados(e['huella'])[8],max(altura_suelo(*p) for p in e['huella']))
for a,b in zip((22,31,40,49),(31,40,49,58)):
    cable_curvo(c,f.punto(a,3.30,.12),f.punto(b,3.30,.12),flecha=.035,radio=.008,segmentos=8)
c.objeto(col)
# Farol del museo, delante del acceso central (130904/130916).
e=edificio(MANZANA,'E02ae75');f=Fachada(None,lados(e['huella'])[5],0)
p=f.punto(f.largo*.5-.4,0,1.2)
farol_pie('M061_postes_farol_museo',p.x,p.y,col,alto=3.5)
# Poste de Universidad en la esquina de Dalence, no junto a Guadalupe.
e=edificio(MANZANA,'E311863');f=Fachada(None,lados(e['huella'])[8],0)
from tendidos_codex import bvh_coleccion,acometida
arbol_col=bvh_coleccion(col)
c,p=poste_vereda('M061_postes_esquina',f,.9,col,doble=True)
c.objeto(col)
c=Constructor('M061_cables_acometidas_esquina')
for k in range(6):
    q=f.punto(15.0,0,-.3);q.z=altura_suelo(q.x,q.y)+5.4+k*.05
    # Exactamente encima de cada aislador de la cruceta, no entre ellos.
    ds=.12+k*.35-1
    a=(p[0]+f.u.x*ds,p[1]+f.u.y*ds,p[2])
    acometida(c,arbol_col,a,q,flecha=.5)
c.objeto(col)
# El frente está retranqueado respecto al límite de la vereda; colocar
# el mástil junto al bordillo real, separado del otro poste y sus brazos.
semaforo_esquina('M061_semaforo_esquina',trasladar(f,d=1.2),1.8,col)
from dalence_codex import mobiliario_dalence
mobiliario_dalence(MANZANA,col)
from ucb_dalence import tendidos
tendidos(edificio(MANZANA,'E311863'),col)
exportar(AGENTE,MANZANA)
