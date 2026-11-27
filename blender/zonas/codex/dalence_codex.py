"""Dalence, R0080–R0086. Inventario previo en INVENTARIO_DALENCE.md.
Una función por edificio; lados recortados, patio abierto y profundidad real.
"""
import math
from kit import *
from mathutils import Vector
from piezas_codex import prisma_seguro,recorte_estricto,trasladar,rama,ventana_rebajada,arbol_podado
from frentes_codex import frente_real,roseta,farol_muro
from detalles_plaza_codex import ajustar_fachada,punto_encadenado
from casas_codex import _cortar
BLANCO='#eeeae3';GRIS='#a9b0b6';PIEDRA='#ad9078';HIERRO='#303a37';VERDE='#697875';ROJO='#804a3b'
# Ojos originales del revisor; solo mirada/FOV ajustados al encuadre de la foto
# ultrangular. El centro del marco original apuntaba al acceso o a una esquina.
MIRADAS_DALENCE={80:(-344.26,-319.74,65.7),81:(-342,-312,65.5),
 82:(-343,-320,66.8),83:(-332,-326,65.5),84:(-330,-329,66.8),
 85:(-322.4,-338.3,66.6),86:(-320.3,-339,66.5)}


def unir_constructor(destino,origen):
    """Conserva materiales al unir frentes deformados al único objeto del edificio."""
    mapa={v:destino.bm.verts.new(v.co) for v in origen.bm.verts}
    indices=[]
    for nombre in origen.mats:
        rol,_,color=nombre.partition('__');indices.append(destino._idx(rol,'#'+color if color else None))
    for f in origen.bm.faces:
        nf=destino.bm.faces.new([mapa[v] for v in f.verts]);nf.material_index=indices[f.material_index]
    origen.bm.free()


def decorar(c,h,z,normal,funcion):
    d=Constructor('frente_temporal');f,g=frente_real({'huella':h},d,z,normal)
    funcion(f);ajustar_fachada(d,g);unir_constructor(c,d)
    return Fachada(None,{'a':tuple(f.a[:2]),'b':tuple(f.punto(f.largo,0)[:2]),'normal':tuple(f.n[:2])},z)


def balaustres(f,a,b,h,d=.31):
    f.caja(a,b,h-.13,h,0,d+.08,'moldura',BLANCO)
    f.caja(a,b,h+.68,h+.80,d-.10,d+.10,'moldura',BLANCO)
    n=max(2,round((b-a)/.40))
    perfil=((0,.045),(.14,.045),(.30,.085),(.46,.04),(.69,.045))
    for k in range(n):
        s=a+(k+.5)*(b-a)/n
        for (h0,r0),(h1,r1) in zip(perfil,perfil[1:]):
            for j in range(3):
                u=j*math.tau/3;v=(j+1)*math.tau/3
                f.c.poligono([f.punto(s+r0*math.cos(u),h+h0,d+r0*math.sin(u)),
                  f.punto(s+r0*math.cos(v),h+h0,d+r0*math.sin(v)),
                  f.punto(s+r1*math.cos(v),h+h1,d+r1*math.sin(v)),
                  f.punto(s+r1*math.cos(u),h+h1,d+r1*math.sin(u))],'moldura',BLANCO)
    for s in (a,b):f.caja(s-.07,s+.07,h,h+.8,d-.09,d+.09,'moldura',BLANCO)


def marco_cartela(f,s,h,w=1.1,H=1.55):
    for a,b,x,y in ((s-w/2,s-w/2+.06,h,h+H),(s+w/2-.06,s+w/2,h,h+H),
                    (s-w/2,s+w/2,h,h+.06),(s-w/2,s+w/2,h+H-.06,h+H)):
        f.caja(a,b,x,y,.02,.08,'moldura',BLANCO)
    roseta(f,s,h+H*.52,.32,color=BLANCO,d=.11)
    for signo in (-1,1):
        f.arco(s+signo*.23,.18,.035,h+H*.52,.04,.12,'moldura',BLANCO,medio=False,segmentos=10)


def zocalo_asamblea(f):
    zocalo(f,1.55,desde=-1,color=PIEDRA,sillares=True)
    for s in (f.largo*.25,f.largo*.75):
        f.caja(s-.34,s+.34,.47,.99,.065,.085,'hierro',HIERRO)
        for ds in (-.2,0,.2):f.caja(s+ds-.012,s+ds+.012,.48,.98,.086,.105,'hierro',HIERRO)
    # Franja de almohadillas piramidales ligada al paramento.
    N=max(2,round(f.largo/.93))
    for k in range(N):
        s=(k+.5)*f.largo/N;r=f.largo/N*.43
        f.caja(s-r,s+r,1.65,2.22,.015,.045,'moldura',BLANCO)
        ps=[f.punto(s-r+.04,1.70,.05),f.punto(s+r-.04,1.70,.05),
            f.punto(s+r-.04,2.17,.05),f.punto(s-r+.04,2.17,.05)]
        centro=f.punto(s,1.935,.17)
        for a,b in zip(ps,ps[1:]+ps[:1]):f.c.poligono([a,b,centro],'moldura',BLANCO)
    for hh in (1.5,2.25,5.68,5.88):cornisa(f,hh,alto=.12,vuelo=.18,color=BLANCO)


def bandas_pb(f,vanos):
    limites=[0]+[x for s,w in vanos for x in (s-w/2-.07,s+w/2+.07)]+[f.largo]
    for j in range(0,len(limites)-1,2):
        a,b=limites[j:j+2]
        if b<=a:continue
        for hh in (2.45,3.07,3.69,4.31,4.93):
            f.caja(a,b,hh,hh+.30,.015,.105,'moldura',BLANCO)


def ventana_asamblea(f,s,h,w=1.7,H=3.0,arco=False):
    ff=trasladar(f,d=.02)
    if arco:ventana_rebajada(ff,s,h,ancho=w,alto=H,reja=h<6,color_moldura=BLANCO,color_carpinteria=ROJO)
    else:ventana(ff,s,h,ancho=w,alto=H,reja=h<6,color_carpinteria=ROJO,color_moldura=BLANCO)
    cornisa(f,h+H+.08,s0=s-w*.7,s1=s+w*.7,alto=.13,vuelo=.18,color=BLANCO)
    if arco:
        roseta(f,s,h+H+.36,.13,color=BLANCO,d=.11)
        for signo in (-1,1):
            f.arco(s+signo*.35,.17,.03,h+H+.26,.04,.12,'moldura',BLANCO,medio=False,segmentos=8)


def frente_asamblea(f,corto=False,alto=True):
    L=f.largo;zocalo_asamblea(f)
    n=2 if corto else max(2,round(L/4.6));ejes=[(k+.5)*L/n for k in range(n)]
    vanos=[(s,1.65) for s in ejes];bandas_pb(f,vanos)
    for s in ejes:
        ventana_asamblea(f,s,2.55,1.65,2.95,arco=not corto)
        ventana_asamblea(f,s,6.55,1.75,3.45,arco=True)
        if alto:ventana_asamblea(f,s,11.65,1.7,2.7)
    for hh in ((5.98,10.85) if alto else (5.98,)):
        if corto:
            if hh<10:balaustres(f,1.05,L-1.05,hh)
            else:
                balaustres(f,.95,L/2-.62,hh);balaustres(f,L/2+.62,L-.95,hh)
                f.caja(L/2-.62,L/2+.62,hh-.05,hh+.8,-.02,.39,'muro',GRIS)
                marco_cartela(trasladar(f,d=.40),L/2,hh+.07,1.05,.61)
            for ss in (.55,L-.55):f.caja(ss-.48,ss+.48,hh-.06,hh+.8,-.02,.42,'muro',GRIS)
        else:balaustres(f,.18,L-.18,hh)
    H=16.15 if alto else 11.35
    for hh,v in ((H-.52,.18),(H-.29,.26),(H-.09,.34)):
        cornisa(f,hh,alto=.14,vuelo=v,color=BLANCO)
    # Friso con óvalos contados por el ancho de cada paño.
    for j in range(max(3,round(L/.59))):
        s=(j+.5)*L/max(3,round(L/.59))
        f.caja(s-.23,s+.23,H-.99,H-.57,.015,.045,'moldura',BLANCO)
        f.c.poligono([f.punto(s+ds,H+hh,.046) for ds,hh in ((-.21,-.97),(.21,-.97),(.21,-.59),(-.21,-.59))],'moldura',GRIS)
        f.c.poligono([f.punto(s+.145*math.cos(k*math.tau/12),H-.78+.115*math.sin(k*math.tau/12),.047) for k in range(12)],'moldura',BLANCO)
    if corto:
        for s in (.55,L-.55):
            pilastra(f,s,6.05,15.15,ancho=.55,vuelo=.16,color=BLANCO)
            for hh in [6.1+j*.48 for j in range(7)]:
                f.caja(s-.33,s+.33,hh,hh+.19,.16,.23,'moldura',BLANCO)
            for ds in (-.15,-.075,0,.075,.15):
                f.caja(s+ds-.012,s+ds+.012,9.55,14.85,.16,.18,'moldura',GRIS)
            for ds in (-.23,0,.23):roseta(f,s+ds,14.98,.13,color=BLANCO,d=.20)
            marco_cartela(trasladar(f,d=.43),s,6.05,.77,.62)
        for hh in (7.25,12.05):marco_cartela(f,L/2,hh,1.10,1.45)
        cornisa(f,9.1,s0=L/2-.7,s1=L/2+.7,alto=.12,vuelo=.16,color=BLANCO)


def asamblea(e,col):
    h=recorte_estricto(e['huella']);c=Constructor(e['id'])
    fd,g=frente_real({'huella':h},c,normal=(-.65,-.76))
    p=fd.punto(fd.largo/2,0);z=altura_suelo(p.x,p.y)
    prisma_seguro(c,h,min(altura_suelo(*p) for p in h)-.5,z+11.35,'muro',GRIS)
    ls=lados(h);l=max((l for l in ls if l['normal'][0]<-.7 and l['normal'][1]>.5 and l['largo']<30),key=lambda l:l['largo'])
    a=l['a'];u=((l['b'][0]-a[0])/l['largo'],(l['b'][1]-a[1])/l['largo'])
    esquina=_cortar(h,a,u,0,1)
    prisma_seguro(c,esquina,z+11.35,z+16.15,'muro',GRIS)
    frentes=[decorar(c,h,z,(-.65,-.76),lambda f:frente_asamblea(f,corto=True))]
    def argentina(f):
        from plaza_este import tramo
        corte=f.largo-l['largo']
        frente_asamblea(tramo(f,0,corte),alto=False)
        frente_asamblea(tramo(f,corte,f.largo),alto=True)
    frentes.append(decorar(c,h,z,(-.76,.65),argentina))
    # Retorno hacia el patio: ventanas rojizas con profundidad, sin ornato inventado.
    lret=max((l for l in ls if l['normal'][0]>.7 and l['normal'][1]<-.5),key=lambda l:l['largo'])
    f=Fachada(c,lret,z)
    for s in (3.5,9.5,15.5):
        for hh in (3.0,7.2,12.0):
            ventana(trasladar(f,d=.02),s,hh,ancho=1.25,alto=2.1,color_carpinteria=ROJO,color_moldura=BLANCO)
    c.objeto(col)
    return frentes


def aro_reja(f,s,h,rx=.23,ry=.18,d=.08):
    for k in range(12):
        a=k*math.tau/12;b=(k+1)*math.tau/12
        rama(f.c,f.punto(s+rx*math.cos(a),h+ry*math.sin(a),d),
             f.punto(s+rx*math.cos(b),h+ry*math.sin(b),d),.016,.016,'hierro',HIERRO)


def reja_patio(f,a,b,h,H=2.8):
    for hh in (h,h+.3,h+H-.4,h+H):f.caja(a,b,hh,hh+.045,.01,.10,'hierro',HIERRO)
    f.caja(a,b,h,h+.29,.02,.055,'hierro',HIERRO)
    for i in range(max(2,round((b-a)/.20))+1):
        s=a+i*(b-a)/max(2,round((b-a)/.20))
        f.cilindro_vertical(s,h,h+H,.06,.014,'hierro',HIERRO,lados=4)
    for i in range(max(1,round((b-a)/.85))):
        s=a+(i+.5)*(b-a)/max(1,round((b-a)/.85))
        aro_reja(f,s,h+H-.18,rx=.32,ry=.13)
        for hh in (h+.7,h+1.65):aro_reja(f,s,hh,rx=.14,ry=.45)
    for s in (a,b,(a+b)/2):f.caja(s-.035,s+.035,h,h+H+.06,-.01,.12,'hierro',HIERRO)


def pabellon_curvo(c,f,masa):
    s0=7.2;d0=-18;r=3.25
    from dalence_huellas_codex import huella_pabellon_m060
    h=huella_pabellon_m060()
    pc=f.punto(s0,0,d0);z=altura_suelo(pc.x,pc.y)+.2
    from triangulacion_codex import triangular_huella
    for t in triangular_huella(h):masa.poligono([(x,y,z-.45) for x,y in reversed(t)],'muro',BLANCO)
    cima=f.punto(s0,0,d0-.1);cima.z=z+10.8
    for i,(a,b) in enumerate(zip(h,h[1:]+h[:1])):
        masa.poligono([(a[0],a[1],z-.45),(b[0],b[1],z-.45),(b[0],b[1],z+2.3),(a[0],a[1],z+2.3)],'muro',BLANCO)
        masa.poligono([(a[0],a[1],z+2.3),(b[0],b[1],z+2.3),(b[0],b[1],z+9.27),(a[0],a[1],z+9.27)],'vidrio' if i<16 else 'muro','#7a918e' if i<16 else BLANCO)
        masa.poligono([(a[0],a[1],z+9.27),(b[0],b[1],z+9.27),cima],'teja','#b46c50')
    for k in range(16):
        a=k*math.pi/16;b=(k+1)*math.pi/16
        def p(t,hh,rr=r+.025):
            q=f.punto(s0+rr*math.cos(t),0,d0+rr*math.sin(t));return Vector((q.x,q.y,z+hh))
        c.poligono([p(a,2.3),p(b,2.3),p(b,9.12),p(a,9.12)],'vidrio','#7a918e')
        rama(c,p(a,2.2,r+.05),p(a,9.25,r+.05),.032,.032,'marco_ventana',VERDE)
        for hh in (2.2,3.75,5.25,6.8,8.25,9.25):rama(c,p(a,hh,r+.05),p(b,hh,r+.05),.027,.027,'marco_ventana',VERDE)
        cima=f.punto(s0,0,d0-.1);cima.z=z+10.8
        for j in range(1,5):
            t=j/5;pa=p(a,9.27).lerp(cima,t);pb=p(b,9.27).lerp(cima,t)
            rama(c,pa,pb,.014,.014,'teja','#945b43')
    # Dos gradas y basamento continuo bajo la galería vidriada.
    for hh,d in ((.2,-14.8),(.4,-15.2),(.6,-15.6)):
        f.caja(3.7,10.7,-.2,hh,d-.4,d,'piedra',PIEDRA)


def patio_dalence(e,col):
    from triangulacion_codex import triangular_huella
    # Vacío real entre Asamblea y edificio blanco: no la caja aislada del lienzo.
    from dalence_huellas_codex import huella_patio_m060
    h=recorte_estricto(datos.recortar_a_calles(huella_patio_m060()))
    piso=Constructor('M060_atrio_piso');punto=(-334.5,-327.4);z=altura_suelo(*punto)+.18
    for t in triangular_huella(h):
        piso.poligono([(x,y,altura_suelo(x,y)+.09) for x,y in t],'adoquin','#c6b59a')
    piso.objeto(col,huella=h);c=Constructor(e['id']);c.huella=h
    def cerramiento(f):
        # El portillo queda abierto en el muro, con marco y reja, no una puerta pegada a un macizo.
        for a,b in ((0,.65),(2.4,4.1)):
            f.caja(a,b,-.4,3.55,-.40,0,'zocalo_piedra','#bda080')
        f.caja(.65,2.4,2.95,3.55,-.4,0,'zocalo_piedra','#bda080')
        reja_patio(f,.69,2.36,.25,H=2.7)
        reja_patio(f,4.12,f.largo-.2,.35,H=2.7)
        for ss in (0,4.08,f.largo-.15):
            f.caja(max(0,ss-.13),min(f.largo,ss+.13),-.25,3.15,-.38,0,'piedra',PIEDRA)
        for hh in (3.50,3.63):cornisa(f,hh,s0=0,s1=4.1,alto=.10,vuelo=.10,rol='piedra',color=PIEDRA)
        # Escalones dentro del acceso, sin invadir vereda.
        for j in range(3):f.caja(4.2,f.largo-.3,-.18,.13+j*.13,-.35-j*.36,-j*.36,'piedra',PIEDRA)
    fr=decorar(c,h,z,(-.65,-.76),cerramiento)
    c.objeto(col)
    c=Constructor('M060_galeria')
    from dalence_huellas_codex import marco_patio_m060
    f=Fachada(c,marco_patio_m060(),z)
    # Galería cálida de tres niveles detrás del muro izquierdo.
    p=f.punto(2.7,0,-7);q=f.punto(2.7,0,-25)
    fg=Fachada(c,{'a':tuple(p[:2]),'b':tuple(q[:2]),'normal':tuple(f.u[:2])},z)
    for hh in (0,3.3,6.6,9.8):fg.caja(0,fg.largo,hh-.20,hh,-2.0,.05,'muro','#ccb497')
    fg.caja(0,fg.largo,-.5,9.8,-2.0,-1.8,'muro','#cdb398')
    for hh in (0,3.3,6.6):
        for j in range(6):
            ss=j*fg.largo/5
            pilastra(fg,ss,hh-.12,hh+3.15,ancho=.25,vuelo=.10,color='#e1cbb0')
        if hh>0:balaustres(fg,.12,fg.largo-.12,hh,d=.10)
        for j in range(5):
            ss=(j+.5)*fg.largo/5
            ventana(trasladar(fg,d=-1.77),ss,hh+.7,ancho=1.3,alto=1.85,color_moldura='#ead9be')
    alero_tejas(fg,9.85,vuelo=.25,fondo=2.3)
    c.huella=[tuple(fg.punto(s,0,d)[:2]) for s,d in ((-.25,-2.35),(fg.largo+.25,-2.35),(fg.largo+.25,.35),(-.25,.35))]
    c.objeto(col)
    c=Constructor('M060_pabellon_detalles');masa=Constructor('M060_pabellon')
    f.c=c
    pabellon_curvo(c,f,masa)
    from dalence_huellas_codex import huella_pabellon_m060
    masa.objeto(col,huella=huella_pabellon_m060());c.objeto(col,huella=huella_pabellon_m060(margen=.35))
    return [fr,fg]


def arco_verde(f,s,h,w,H,d=.025):
    # Ventanal de medio punto con montantes y paños a varias alturas.
    r=w/2;arr=h+H-r
    f.caja(s-r,s+r,h,arr,d,d+.025,'vidrio','#83948e')
    f.timpano_arco(s,r,arr,d+.025,'vidrio','#83948e')
    for signo in (-1,1):f.caja(s+signo*r-.055,s+signo*r+.055,h,arr,d,d+.12,'marco_ventana',HIERRO)
    f.arco(s,r,.065,arr,d+.025,d+.12,'marco_ventana',HIERRO,segmentos=20)
    for hh in [h+j*1.25 for j in range(1,max(2,math.ceil((H-r)/1.25)))]:
        if hh<arr:f.caja(s-r,s+r,hh,hh+.045,d+.05,d+.13,'marco_ventana',HIERRO)
    f.caja(s-.025,s+.025,h,h+H-.06,d+.06,d+.13,'marco_ventana',HIERRO)
    # Cortinas claras, remetidas respecto a los montantes.
    for signo in (-1,1):f.caja(s+signo*r*.67-.12,s+signo*r*.67+.12,h+.14,arr-.08,d+.029,d+.035,'vidrio','#b5b4a8')
    cornisa(f,h-.08,s0=s-r-.08,s1=s+r+.08,alto=.09,vuelo=.12,rol='piedra',color=VERDE)


def hexagonal(f,s,h,w=.5,H=2.5):
    def puntos(w,H,h,d):
        return [f.punto(s,h,d),f.punto(s+w/2,h+.32,d),f.punto(s+w/2,h+H-.32,d),
                f.punto(s,h+H,d),f.punto(s-w/2,h+H-.32,d),f.punto(s-w/2,h+.32,d)]
    f.c.poligono(puntos(w+.12,H+.14,h-.07,.08),'marco_ventana',HIERRO,grosor=.03,normal_extrusion=-f.n)
    f.c.poligono(puntos(w,H,h,.105),'vidrio','#3c4842')
    for ds in (-w*.24,0,w*.24):f.caja(s+ds-.009,s+ds+.009,h+.29,h+H-.29,.106,.135,'hierro',HIERRO)


def balconera_moderno(f,s,h,ancho,alto):
    """Carpintería granate con paños bajos lisos, sin rosetas inventadas."""
    ventana_rebajada(f,s,h,ancho=ancho,alto=alto,color_moldura=GRIS,color_carpinteria='#673445')
    r=ancho/2
    f.caja(s-r,s+r,h,h+.70,.02,.06,'madera','#673445')
    for signo in (-1,1):
        centro=s+signo*ancho*.24
        for hh in (h+.12,h+.56):f.caja(centro-ancho*.19,centro+ancho*.19,hh,hh+.035,.061,.075,'marco_ventana','#714236')


def frente_moderno(f):
    L=f.largo;k=L/20
    # Medidas horizontales se escalan solo al ancho real de la cadena recortada.
    def s(x):return x*k
    zocalo(f,4.0,s1=s(13.6),desde=-.6,color='#c9955f',sillares=True)
    zocalo(f,1.20,s0=s(13.6),desde=-.6,color='#b39878',sillares=True)
    for ss in (1.25,3.4):
        ventana(trasladar(f,d=.09),s(ss),1.0,ancho=1.2*k,alto=2.6,reja=True,color_carpinteria=HIERRO,color_moldura=PIEDRA)
        arco_verde(f,s(ss),4.2,1.35*k,6.8)
        arco_verde(f,s(ss),12.05,1.3*k,2.2)
    # Franja central de nueve ranuras de extremos facetados: 3 + 3 + 3.
    for ss in (4.95,5.55,6.15,7.15,7.75,8.35,9.35,9.95,10.55):hexagonal(f,s(ss),1.15,w=.46*k,H=2.45)
    for ss in (5.8,9.0):
        ventana(trasladar(f,d=.02),s(ss),4.65,ancho=1.2*k,alto=2.55,reja=True,color_carpinteria=HIERRO,color_moldura=BLANCO)
        arco_verde(f,s(ss),8.65,1.1*k,2.0)
    # Portón derecho y vano alto; su zócalo se interrumpe visualmente con marco completo.
    puerta(trasladar(f,h=.16,d=.09),s(12.5),ancho=2.5*k,alto=3.6,color=HIERRO,color_moldura=PIEDRA)
    ventana(trasladar(f,d=.02),s(12.5),4.6,ancho=1.2*k,alto=2.55,reja=True,color_carpinteria=HIERRO,color_moldura=BLANCO)
    for ss in (17.65,19.15):
        balconera_moderno(trasladar(f,d=.02),s(ss),8.4,1.05*k,2.2)
        balconera_moderno(trasladar(f,d=.02),s(ss),4.65,1.05*k,2.4)
        for hh in (4.05,7.95):
            f.caja(s(ss)-.65*k,s(ss)+.65*k,hh,hh+.36,.005,.02,'moldura','#c7cbc4')
            f.caja(s(ss)-.57*k,s(ss)+.57*k,hh+.06,hh+.30,.021,.025,'moldura',BLANCO)
    for ss,w in ((17.3,2.0),(19.25,.8)):
        puerta(trasladar(f,h=.13,d=.09),s(ss),ancho=w*k,alto=3.3,color='#4b302b',color_moldura=BLANCO)
    # Torres laterales: izquierda alta y caja de escalera estrecha.
    for a,b,H in ((0,4.55,17.4),(11.4,13.6,14.7)):
        for hh in (H-.34,H-.16):cornisa(f,hh,s0=s(a),s1=s(b),alto=.15,vuelo=.19,color=VERDE)
    arco_verde(f,s(12.5),8.35,1.15*k,5.45)
    for hh in [4.25+j*.45 for j in range(23)]:
        for a,b in ((11.4,11.83),(13.17,13.6)):f.caja(s(a),s(b),hh,hh+.014,.004,.018,'moldura','#adb3ad')
    ventana(trasladar(f,d=.02),s(2.3),15.4,ancho=.9*k,alto=1.3,color_carpinteria=HIERRO,color_moldura=BLANCO)
    f.c.poligono([f.punto(s(2.3)+.55*k*math.cos(j*math.pi/20),17.35+.55*k*math.sin(j*math.pi/20),.035) for j in range(21)],'moldura',VERDE,grosor=.20,normal_extrusion=-f.n)
    for a,b in ((0,4.55),(4.55,11.4),(13.6,20)):
        hh=15.0 if a==0 else (11.2 if a==4.55 else 11.75)
        cornisa(f,hh,s0=s(a),s1=s(b),alto=.21,vuelo=.20,color=VERDE)
    cornisa(f,7.65,s0=s(4.55),s1=L,alto=.22,vuelo=.22,color=VERDE)
    # Mansarda con retícula diagonal apoyada en el cuerpo central.
    a,b=s(4.55),s(11.4)
    f.c.poligono([f.punto(a,11.48,0),f.punto(b,11.48,0),f.punto(b,13.6,-.65),f.punto(a,13.6,-.65)],'metal','#929f98')
    for x in range(math.ceil((b-a)/.22)):
        ss=a+x*.22
        for signo in (-1,1):
            t=min(1,(b-ss)/1.2) if signo>0 else min(1,(ss-a)/1.2)
            if t>.01:rama(f.c,f.punto(ss,11.5,.015),f.punto(ss+signo*1.2*t,11.5+2.1*t,-.65*t+.015),.009,.009,'marco_ventana',VERDE)
    # Lucarna central arrimada a la cubierta inclinada.
    f.caja(s(7.95)-.9,s(7.95)+.9,11.45,12.2,-.65,.02,'muro',BLANCO)
    arco_verde(f,s(7.95),11.5,1.5,1.45,d=.04)


def edificio_moderno(e,col):
    h=recorte_estricto(e['huella']);c=Constructor(e['id']+'_detalles');masa=Constructor(e['id'])
    f,g=frente_real({'huella':h},c,normal=(-.65,-.76))
    p=f.punto(f.largo/2,0);z=altura_suelo(p.x,p.y)
    tramos=[(h,z+11.8)]
    # Torres nacen del cuerpo continuo y conservan apoyo en todo el espesor.
    for a,b,H in ((0,f.largo*4.55/20,17.4),(f.largo*11.4/20,f.largo*13.6/20,14.7)):
        trozo=h if a==0 else _cortar(h,tuple(f.a[:2]),tuple(f.u[:2]),a,1)
        trozo=_cortar(trozo,tuple(f.a[:2]),tuple(f.u[:2]),b,-1)
        if a==0:trozo=_cortar(trozo,tuple(f.a[:2]),tuple(f.n[:2]),-8,1)
        if len(trozo)>2:tramos.append((trozo,z+H))
    from volumenes_codex import cuerpo_escalonado
    from dalence_huellas_codex import huella_patio_m060
    patio=recorte_estricto(datos.recortar_a_calles(huella_patio_m060()))
    cuerpo_escalonado(masa,tramos,min(altura_suelo(*p) for p in h)-.5,BLANCO,vacios=[patio])
    masa.objeto(col,huella=h);c.huella=h
    frente=decorar(c,h,z,(-.65,-.76),frente_moderno)
    # Costado al patio: zócalo portal de piedra y vitrina vertical.
    l=min((l for l in lados(h) if l['normal'][0]<-.9),key=lambda l:l['largo'])
    fp=Fachada(c,l,z)
    zocalo(fp,4.0,desde=-.8,color='#c9955f',sillares=True)
    ventana(trasladar(fp,d=.09),fp.largo*.5,1.1,ancho=1.35,alto=2.6,reja=True,color_carpinteria=HIERRO,color_moldura=PIEDRA)
    ventana(trasladar(fp,d=.02),fp.largo*.5,4.6,ancho=2.1,alto=11.7,color_carpinteria=VERDE,color_moldura=BLANCO)
    for hh in (7.5,10.4,13.3):fp.caja(fp.largo*.5-1.05,fp.largo*.5+1.05,hh,hh+.08,.05,.13,'marco_ventana',VERDE)
    for ss in (.35,fp.largo*.5,fp.largo-.35):
        fp.caja(ss-.13,ss+.13,17.38,17.62,-.28,-.02,'moldura',BLANCO)
        p=fp.punto(ss,17.62,-.15)
        c.cilindro(p.x,p.y,p.z,p.z+.18,.13,'moldura',BLANCO,lados=4,radio_arriba=.025)
    c.objeto(col)
    # Árbol documentado al extremo derecho, alejado de la fachada.
    g['suelo']=z
    p=punto_encadenado(g,g['largo']*17.2/20,0,1.0)
    ultimo=g['lados'][-1];tangente=Vector((ultimo['b'][0]-ultimo['a'][0],ultimo['b'][1]-ultimo['a'][1],0)).normalized()
    normal=Vector((*ultimo['normal'],0))
    arbol=Constructor('M061_arbol_Dalence');suelo=altura_suelo(p.x,p.y)
    from varillas_codex import rama as ramita
    from ucb_dalence import hojas_ralas
    base=Vector((p.x,p.y,suelo-.15));bifurcacion=Vector((p.x+.12,p.y,suelo+2.55))
    ramita(arbol,base,bifurcacion,.11,.07,'tronco','#68503c')
    for j in range(12):
        ang=j*2.39996;radio=1.2+(j%3)*.27
        q=p+tangente*(radio*math.cos(ang))+normal*(.32*math.sin(ang));q.z=suelo+4.55+(j%4)*.40
        ramita(arbol,bifurcacion,q,.035,.010,'tronco','#68503c')
        hojas_ralas(arbol,q,tangente,normal,890+j)
        colgante=q+Vector((0,0,-.24))
        ramita(arbol,q,colgante,.010,.007,'tronco','#68503c')
        hojas_ralas(arbol,colgante,tangente,normal,990+j)
    arbol.objeto(col)
    return [frente,fp]


def anclajes_poste(mid):
    eid,ss={'M055':('Eae1b1b',None),'M061':('E00e8b2',7.0)}[mid]
    e=edificio(mid,eid);h=recorte_estricto(e['huella'])
    f,g=frente_real({'huella':h},None,normal=(-.65,-.76))
    ss=g['largo']-.5 if ss is None else ss
    p=punto_encadenado(g,ss,0,1.6 if mid=='M061' else .95)
    resto=ss
    for l in g['lados']:
        if resto<=l['largo']:break
        resto-=l['largo']
    u=Vector((l['b'][0]-l['a'][0],l['b'][1]-l['a'][1],0)).normalized()
    n=Vector((*l['normal'],0));z=altura_suelo(p.x,p.y)
    p.z=z
    return p,u,n,[p+u*(-.8+j*.32)+Vector((0,0,8.5)) for j in range(6)]


def mobiliario_dalence(mid,col):
    """Dos postes documentados y seis vanos entre sus aisladores, comprobados por rayos."""
    import bpy
    from tendidos_codex import bvh_coleccion
    from piezas_codex import cable_curvo
    p,u,n,puntas=anclajes_poste(mid)
    c=Constructor(mid+'_Dalence_postes')
    c.cilindro(p.x,p.y,p.z-.25,p.z+8.8,.085,'tronco','#6d5140',lados=10,radio_arriba=.06)
    c.caja_ejes(p+Vector((0,0,8.18)),u,n,(0,0,1),2.0,.13,.12,'metal','#6d5140')
    for q in puntas:
        c.cilindro(q.x,q.y,q.z-.25,q.z,.05,'vidrio','#a8b0a2',lados=6)
        for dh in (-.20,-.12,-.05):c.cilindro(q.x,q.y,q.z+dh,q.z+dh+.03,.07,'vidrio','#929c91',lados=6)
    for hh in (4.5,6.3,7.8):c.cilindro(p.x,p.y,p.z+hh,p.z+hh+.07,.093,'metal','#555a54',lados=10)
    if mid=='M061':
        q=p+n*.22
        c.cilindro(q.x,q.y,p.z+6.4,p.z+7.1,.17,'metal','#777f77',lados=10)
        for hh in (6.45,6.96):c.caja_ejes(p+n*.10+Vector((0,0,hh)),u,n,(0,0,1),.28,.45,.07,'metal',HIERRO)
    c.objeto(col)
    if mid!='M055':return
    # La otra manzana solo se carga para comprobar obstáculos; nunca se exporta aquí.
    contexto=bpy.data.collections.new('comprobar_vanos_Dalence');bpy.context.scene.collection.children.link(contexto)
    for ob in col.all_objects:
        if '_Dalence_poste' not in ob.name and 'arbol' not in ob.name:contexto.objects.link(ob)
    anteriores=set(bpy.data.objects)
    import os
    bpy.ops.import_scene.gltf(filepath=os.path.join(datos.RAIZ,'web/public/models/ciudad/codex/M061.glb'))
    importados=set(bpy.data.objects)-anteriores
    for ob in importados:
        if ob.type=='MESH' and '_Dalence_poste' not in ob.name and 'arbol' not in ob.name:contexto.objects.link(ob)
    arbol=bvh_coleccion(contexto);destinos=anclajes_poste('M061')[3]
    cables=Constructor('M055_Dalence_cables')
    for a,b in zip(puntas,destinos):
        puntos=[]
        for k in range(25):
            t=k/24;q=a.lerp(b,t);q.z-=.45*4*t*(1-t);puntos.append(q)
        for aa,bb in zip(puntos[1:-2],puntos[2:-1]):
            delta=bb-aa
            if arbol.ray_cast(aa,delta.normalized(),delta.length)[0] is not None:raise ValueError('Vano Dalence cruza arquitectura')
        cable_curvo(cables,a,b,flecha=.45,radio=.013,segmentos=24)
    cables.objeto(col)
    for ob in importados:bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.collections.remove(contexto)
    print('[Dalence] Seis vanos conectados y libres de arquitectura',flush=True)
