"""Nave ausente sobre Arenales, #24. Inventario en INVENTARIO_REPASO.md.

130427/31/35/38: muro ciego, un vano alto con bandera, farol, cables y
enredadera. Se añade únicamente la franja delante de Eeb6abd/M037;
la portada y torre existentes no se duplican. Cubierta posterior estimada.
"""
import math
from mathutils import Vector
from kit import *
from piezas_codex import prisma_seguro,recorte_estricto,trasladar,rama,cable_curvo,copa_fina
from frentes_codex import frente_real,farol_muro
from detalles_plaza_codex import ajustar_fachada,punto_encadenado
BLANCO='#eeeae3'


def huella_nave():
    # La trasera coincide exactamente con la arista NE del convento:
    # sumar un prisma completo encima del convento duplicaría volúmenes.
    n=Vector((.637,.771));n.normalize()
    a=Vector((-280.11,-43))-n*5.8
    b=Vector((-252.11,-66.11))-n*5.8
    e=edificio('M037','Eeb6abd')
    aa,bb=Vector(e['huella'][-2]),Vector(e['huella'][-1])
    def cruz(p,q):return p.x*q.y-p.y*q.x
    u=bb-aa
    def trasera(p):return p-n*(cruz(p-aa,u)/cruz(n,u))
    h=[tuple(a),tuple(b),tuple(trasera(b)),tuple(trasera(a))]
    return recorte_estricto(datos.recortar_a_calles(h))


def construir_nave(col):
    h=huella_nave();c=Constructor('M037_SanMiguel_nave_Arenales')
    z=max(altura_suelo(*p) for p in h);zb=min(altura_suelo(*p) for p in h)-.4
    f,g=frente_real({'huella':h},c,z,normal=(.637,.771));L=f.largo;H=9.5
    # Un solo vano alto al extremo del atrio; el resto es muro ciego.
    s=2.1
    ventana(trasladar(f,d=.025),s,6.05,ancho=1.0,alto=1.45,reja=True,
            color_carpinteria='#593b31',color_moldura=BLANCO)
    for hh,alto,vuelo in ((9.12,.10,.10),(9.25,.13,.17),(9.42,.08,.22)):
        cornisa(f,hh,alto=alto,vuelo=vuelo,color=BLANCO)
    # Zócalo mínimo que sigue el terreno, sin basamento alto inventado.
    for k in range(math.ceil(L)):
        ss=min(L-.01,k+.5);p=f.punto(ss,0)
        hh=altura_suelo(p.x,p.y)-z
        f.caja(k,min(L,k+1),hh-.2,hh+.20,-.015,.025,'zocalo_piedra','#d0c5b2')
    # Salientes fotografiados bajo la cornisa; conectados al muro.
    for ss in (L*.33,L*.76):
        rama(c,f.punto(ss,8.55,-.06),f.punto(ss,8.48,.38),.07,.085,'moldura',BLANCO)
    farol_muro(f,.65,5.0)
    # Asta oblicua y paño colgante de tres franjas conectado a ella.
    p=f.punto(s-.1,7.4,.07);q=f.punto(s-.1,7.8,.66)
    rama(c,p,q,.018,.018,'madera','#785439')
    for j,color in enumerate(('#b8493c','#ddba4b','#527a44')):
        hh=7.8-j*.32
        c.poligono([f.punto(s-.10,hh,.66),f.punto(s+.36,hh-.04,.43),
                    f.punto(s+.36,hh-.36,.43),f.punto(s-.10,hh-.32,.66)],
                    'pintura_acento',color,grosor=.008,normal_extrusion=f.n)
    # Haz unido a grampas; no son cables libres atravesando la nave.
    for j in range(5):
        hh=4.45+j*.075;d=.13+j*.013
        for a,b in zip((0,L*.33,L*.66),(L*.33,L*.66,L)):
            cable_curvo(c,f.punto(a,hh,d),f.punto(b,hh,d),flecha=.06,radio=.012,segmentos=8)
    for ss in (0,L*.33,L*.66,L):
        rama(c,f.punto(ss,4.42,-.01),f.punto(ss,4.78,.22),.026,.026,'hierro','#40433b')
    ajustar_fachada(c,g)
    prisma_seguro(c,h,zb,z+H,'muro',BLANCO)
    c.objeto(col)
    # Dos faldones con cumbrera paralela a calle; cara inferior apoyada.
    # La trasera del convento ya existe: el tejado se limita a la franja nueva.
    c=Constructor('M037_SanMiguel_cubierta_Arenales')
    # Usar el mismo frente real y deformar cada pieza al quiebre de la calle.
    ff,gg=frente_real({'huella':h},c,z,normal=(.637,.771))
    # Alero sobre la guía, antes de añadir los faldones en coordenadas reales.
    alero_tejas(ff,H,vuelo=.22,fondo=.7,pendiente=16)
    ajustar_fachada(c,gg)
    # Dos aguas contenidas en la huella mediante secciones interiores.
    # Los faldones se construyen por cada triángulo de la huella con
    # altura en función de la distancia al frente y la trasera real.
    from triangulacion_codex import triangular_huella
    from pavimentos_codex import _partir
    fa=Vector((*g['lados'][0]['a'],0));normal=Vector((*g['lados'][0]['normal'],0))
    def prof(p):return -(Vector((*p,0))-fa).dot(normal)
    fondo=max(prof(p) for p in h);mitad=fondo/2
    for tri in triangular_huella(h):
        izq,der=_partir(list(tri),lambda p:mitad-prof(p))
        for pol in (izq,der):
            if len(pol)<3:continue
            pts=[(x,y,z+H+.03+2.0*max(0,1-abs(prof((x,y))-mitad)/mitad)) for x,y in pol]
            c.poligono(pts,'teja','#a96349')
    c.objeto(col)
    # Enredadera adherida al extremo del atrio, sin copa maciza flotante.
    c=Constructor('M037_SanMiguel_enredadera')
    ss=.14
    for j in range(19):
        hh=.3+j*.26;p=punto_encadenado(g,ss+.12*math.sin(j*.8),hh,.10)
        q=punto_encadenado(g,ss+.12*math.sin((j+1)*.8),hh+.27,.10)
        rama(c,p,q,.018,.012,'tronco','#685744')
        if j>4:copa_fina(c,p.x,p.y,p.z,.16,.16,.16,semilla=171+j)
    c.objeto(col)
    f.punto=lambda s,h,d=0:punto_encadenado(g,s,h,d)
    return f
