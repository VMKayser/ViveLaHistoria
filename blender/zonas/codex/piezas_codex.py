"""Geometría local de Codex; no modifica el kit compartido."""
import math
from kit import Fachada, arqueria


def trasladar(f, h=0, d=0):
    return Fachada(f.c, {'a':tuple(f.punto(0,0,d)[:2]),
        'b':tuple(f.punto(f.largo,0,d)[:2]),'normal':tuple(f.n[:2])},f.suelo+h)


def recortar_interior(huella, f, limite):
    """Recorta un polígono al semiplano d <= limite, conservando la huella."""
    salida=[]
    def distancia(p):return (p[0]-f.a.x)*f.n.x+(p[1]-f.a.y)*f.n.y-limite
    for a,b in zip(huella,huella[1:]+huella[:1]):
        da,db=distancia(a),distancia(b)
        if da<=0:salida.append(a)
        if (da<=0)!=(db<=0):
            t=da/(da-db)
            salida.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    return salida


def campanario(f,h0,h1):
    """Dos arcos realmente abiertos: pilares, enjutas y campanas interiores."""
    w=f.largo
    pilar=w*.16
    luz=(w-3*pilar)/2
    arranque=h1-h0-1.1-luz/2
    f.caja(0,w,h0,h0+.8,-.55,0,'muro','#eeeae2')
    ff=trasladar(f,h=h0+.8)
    arqueria_lisa_codex(ff,0,2,luz,arranque,pilar=pilar,d0=-.55,d1=0,
             alto_total=h1-h0-.8, color='#eeeae2')
    for s in (pilar+luz/2,2*pilar+1.5*luz):
        f.caja(s-luz/2-.08,s+luz/2+.08,h0+arranque+.45,h0+arranque+.62,-.55,-.1,'madera')
        p=f.punto(s,h0+arranque+.45-.95,-.5)
        f.c.cilindro(p.x,p.y,p.z,p.z+.95,.43,'metal','#777061',lados=12,radio_arriba=.2)
        f.c.cilindro(p.x,p.y,p.z-.08,p.z+.08,.47,'metal','#777061',lados=12)
        f.c.cilindro(p.x,p.y,p.z-.22,p.z+.4,.045,'hierro',lados=6)
        f.c.cilindro(p.x,p.y,p.z+.90,p.z+1.06,.045,'hierro',lados=6)


def reja_porton(f,s,ancho=2.7,alto=2.8):
    for k in range(15):
        x=s-ancho/2+ancho*k/14
        cima=alto+.45*math.sin(math.pi*k/14)
        f.cilindro_vertical(x,0,cima,.02,.022,'hierro',lados=6)
    for h in (.15,1.15,2.4):f.caja(s-ancho/2,s+ancho/2,h,h+.045,0,.06,'hierro')
    for fila in range(3):
        for k in range(6):
            f.arco(s-ancho/2+.25+k*.44,.18,.025,.5+fila*.75,0,.05,'hierro',segmentos=8,medio=False)


def juntas(f,h0,h1,s0,s1,paso=.5):
    """Juntas cortas de sillería: relieve claro, sin sombra pintada."""
    for j in range(int((h1-h0)/paso)+1):
        h=h0+j*paso
        f.caja(s0,s1,h,h+.018,.012,.027,'piedra','#ccb18f')
        for k in range(int((s1-s0)/.8)+1):
            s=s0+k*.8+(.4 if j%2 else 0)
            if s<s1:f.caja(s,s+.018,h,min(h+paso,h1),.012,.027,'piedra','#ccb18f')


def prisma_seguro(c,huella,z0,z1,rol='muro',color=None):
    """Muros y cubierta triangulada en 2D: evita diagonales fuera de huellas cóncavas."""
    from triangulacion_codex import triangular_huella
    c.prisma(huella,z0,z1,rol,color,tapa=False)
    for tri in triangular_huella(huella):
        c.poligono([(x,y,z1) for x,y in tri],rol if rol in ('piedra','adoquin','zocalo_piedra') else 'azotea',color if rol in ('piedra','adoquin','zocalo_piedra') else None)


def copa_elipsoide(c,x,y,z,rx,ry,rz,rol='follaje',color=None):
    """Masa vegetal baja y ancha para árboles podados, sin textura fotográfica."""
    for j in range(8):
        a=-math.pi/2+j*math.pi/8
        b=a+math.pi/8
        for k in range(18):
            u=k*math.tau/18;v=(k+1)*math.tau/18
            def p(t,w):return (x+rx*math.cos(t)*math.cos(w),y+ry*math.cos(t)*math.sin(w),z+rz*math.sin(t))
            ps=[p(a,u),p(a,v),p(b,v),p(b,u)]
            # Polos: una sola cara triangular, sin vértices repetidos.
            if j==0:ps=[ps[0],ps[2],ps[3]]
            if j==7:ps=[ps[0],ps[1],ps[2]]
            c.poligono(ps,rol,color)


def objeto_vegetal(c,col):
    """Suavizar solo follaje después de crear el objeto: el kit aplana normales."""
    ob=c.objeto(col)
    for cara in ob.data.polygons:
        material=ob.data.materials[cara.material_index]
        if material.name.split('__')[0] in ('follaje','follaje_claro'):
            cara.use_smooth=True
    return ob


def arbol_podado(nombre,x,y,col,radio=1.7,alto=3.6,direccion=None):
    """Paraguas podado: tronco bifurcado y copa de bordes menudos, foto de plaza.

    Con direccion, la copa se alarga a lo largo de la vereda y mantiene libre
    el balcón. No se colocan masas de follaje por detrás de la fachada.
    """
    from kit import Constructor,altura_suelo
    import random
    azar=random.Random(round(x*1000)+round(y*1000))
    c=Constructor(nombre);z=altura_suelo(x,y)
    nx,ny=direccion or (0,1);ux,uy=-ny,nx
    def p(s,d,h):return (x+ux*s+nx*d,y+uy*s+ny*d,z+h)
    rama(c,p(0,0,0),p(.04,0,alto*.57),.13,.085)
    c.cilindro(x,y,z,z+.5,.135,'muro','#d4d3bf',lados=8,radio_arriba=.12)
    for k in range(5):
        a=k*math.tau/5+.23
        ss=math.cos(a)*radio*.65;dd=math.sin(a)*min(.58,radio*.4)
        rama(c,p(.04,0,alto*.52),p(ss,dd,alto-.15),.075,.025)
    for k in range(15):
        a=k*2.39996;rr=math.sqrt((k+.5)/15)
        ss=math.cos(a)*rr*radio;dd=math.sin(a)*rr*min(.57,radio*.48)
        cx,cy,cz=p(ss,dd,alto+azar.uniform(-.13,.18))
        # Copa de contorno menudo: cinco anillos y diez sectores.
        rx=radio*(.32+azar.random()*.12);ry=min(.37,radio*.27);rz=.3+azar.random()*.13
        for j in range(5):
            aa=-math.pi/2+j*math.pi/5;bb=aa+math.pi/5
            for t in range(10):
                u=t*math.tau/10;v=(t+1)*math.tau/10
                def q(hh,ww):
                    sx=rx*math.cos(hh)*math.cos(ww);dy=ry*math.cos(hh)*math.sin(ww)
                    return (cx+ux*sx+nx*dy,cy+uy*sx+ny*dy,cz+rz*math.sin(hh))
                pts=[q(aa,u),q(aa,v),q(bb,v),q(bb,u)]
                if j==0:pts=[pts[0],pts[2],pts[3]]
                if j==4:pts=[pts[0],pts[1],pts[2]]
                c.poligono(pts,'follaje',('#486737','#54763b','#617f40','#4e7039')[k%4])
    return objeto_vegetal(c,col)


def farol_pie(nombre,x,y,col,alto=3.5):
    from kit import Constructor,altura_suelo
    c=Constructor(nombre);z=altura_suelo(x,y)
    for h0,h1,r in ((0,.12,.22),(.12,.35,.14),(.35,alto-.65,.055)):
        c.cilindro(x,y,z+h0,z+h1,r,'hierro',lados=8)
    c.cilindro(x,y,z+alto-.65,z+alto-.2,.19,'vidrio','#b7b0a0',lados=4,radio_arriba=.25)
    c.cilindro(x,y,z+alto-.20,z+alto,.32,'hierro',lados=4,radio_arriba=.035)
    for dx,dy in ((-.14,-.14),(-.14,.14),(.14,-.14),(.14,.14)):
        c.cilindro(x+dx,y+dy,z+alto-.65,z+alto-.17,.02,'hierro',lados=5)
    return c.objeto(col)


def ventana_arco_reja(f,s,h,ancho=1.35,alto=3.0,color_moldura=None):
    """Reja ajustada al arco; los barrotes no salen del hueco sobre el muro."""
    from kit import ventana
    r=ancho/2;arranque=h+alto-r
    ventana(f,s,h,ancho=ancho,alto=alto-r,arco=True,reja=False,color_moldura=color_moldura)
    for k in range(11):
        ds=-r+.06+(ancho-.12)*k/10
        cima=arranque+math.sqrt(max(0,r*r-ds*ds))-.04
        f.cilindro_vertical(s+ds,h+.04,cima,.10,.015,'hierro',lados=4)
    for hh in (h+.12,h+alto*.4,arranque-.08):
        f.caja(s-r,s+r,hh,hh+.03,.09,.12,'hierro')


def ventana_rebajada(f,s,h,ancho=1.3,alto=2.3,reja=False,color_moldura='#eeeae5',panel=False,color_carpinteria='#714335'):
    """Ventana con arco elíptico bajo y carpintería rojiza, tomada de M061."""
    r=ancho/2;arranque=h+alto-.22
    f.caja(s-r,s+r,h,arranque,0,.016,'vidrio')
    if panel:
        # Paños opacos tallados bajo las hojas con cortinas, visibles en M061.
        f.caja(s-r,s+r,h,h+.62,.02,.06,'madera',color_carpinteria)
        for signo in (-1,1):
            a=s-r+.08 if signo<0 else s+.04
            b=s-.04 if signo<0 else s+r-.08
            f.caja(a,b,h+.67,arranque-.04,.021,.027,'vidrio','#c7c3b7')
            f.caja(a,b,h+.10,h+.15,.06,.075,'marco_ventana',color_carpinteria)
            f.arco((a+b)/2,.10,.025,h+.35,.06,.075,'marco_ventana','#865c43',medio=False,segmentos=8)
    puntos=[f.punto(s-r*math.cos(k*math.pi/16),arranque+.22*math.sin(k*math.pi/16),.018)
            for k in range(17)]
    f.c.poligono(puntos,'vidrio')
    for signo in (-1,1):
        ss=s+signo*r
        f.caja(ss-.07,ss+.07,h,arranque,.02,.07,'marco_ventana',color_carpinteria)
        ss=s+signo*(r+.12)
        f.caja(ss-.07,ss+.07,h-.08,arranque,.01,.08,'moldura',color_moldura)
    for k in range(16):
        a=k*math.pi/16;b=(k+1)*math.pi/16
        f.c.poligono([f.punto(s-r*math.cos(a),arranque+.22*math.sin(a),.065),
                       f.punto(s-r*math.cos(b),arranque+.22*math.sin(b),.065),
                       f.punto(s-(r+.14)*math.cos(b),arranque+.34*math.sin(b),.065),
                       f.punto(s-(r+.14)*math.cos(a),arranque+.34*math.sin(a),.065)],
                      'moldura',color_moldura)
    for hh in (h,h+.75,h+1.5):f.caja(s-r,s+r,hh,hh+.055,.02,.055,'marco_ventana',color_carpinteria)
    for ds in (-ancho/4,0,ancho/4):f.caja(s+ds-.025,s+ds+.025,h,arranque,.02,.055,'marco_ventana',color_carpinteria)
    if reja:
        for k in range(9):
            ds=-r+.05+(ancho-.1)*k/8
            cima=arranque+.22*math.sqrt(max(0,1-(ds/r)**2))-.02
            f.cilindro_vertical(s+ds,h+.04,cima,.11,.015,'hierro',lados=4)


def cable_curvo(c,a,b,flecha=.3,radio=.012,segmentos=12):
    """Cable con flecha parabólica; detalle pedido expresamente el 2026-11-06."""
    from mathutils import Vector
    a,b=Vector(a),Vector(b)
    for k in range(segmentos):
        def punto(t):
            p=a.lerp(b,t);p.z-=4*flecha*t*(1-t);return p
        p,q=punto(k/segmentos),punto((k+1)/segmentos)
        direccion=(q-p).normalized();u=direccion.cross(Vector((0,0,1)))
        if u.length<.01:u=Vector((1,0,0))
        u.normalize();v=direccion.cross(u).normalized()
        vs=[u*radio,v*radio,-u*radio,-v*radio]
        for j in range(4):c.poligono([p+vs[j],p+vs[(j+1)%4],q+vs[(j+1)%4],q+vs[j]],'hierro')


def poste_vereda(nombre,f,ss,col,alto=8.5,doble=False):
    from kit import Constructor,altura_suelo
    c=Constructor(nombre);p=f.punto(ss,0,1.3);z=altura_suelo(p.x,p.y)
    if doble:
        for ds in (-.85,.85):
            x,y=p.x+f.u.x*ds,p.y+f.u.y*ds
            c.cilindro(x,y,z,z+alto,.08,'metal','#6c4d3c',lados=8)
        for ds in (-.5,0,.5):
            x,y=p.x+f.u.x*ds,p.y+f.u.y*ds
            c.cilindro(x,y,z+alto-2,z+alto-1.1,.16,'metal','#646967',lados=10)
    else:c.cilindro(p.x,p.y,z,z+alto,.11,'piedra','#b7b3a6',lados=8,radio_arriba=.075)
    ff=Fachada(c,{'a':(p.x-f.u.x,p.y-f.u.y),'b':(p.x+f.u.x,p.y+f.u.y),
                   'normal':tuple(f.n[:2])},z)
    if doble:ff.caja(0,2,alto-2.1,alto-1.98,-.10,.10,'metal')
    ff.caja(0,2,alto-.6,alto-.5,-.08,.08,'metal')
    for k in range(6):
        ff.cilindro_vertical(.12+k*.35,alto-.5,alto-.3,0,.055,'vidrio','#7f9697',lados=6)
    return c,(p.x,p.y,z+alto-.3)


def arqueria_lisa_codex(f,s0,n,luz,h_arranque,pilar=.6,d0=-.55,d1=0,alto_total=None,color='#eeeae2'):
    """Enjutas por paños de borde curvo, sin escalones ni polígonos cóncavos."""
    r=luz/2;alto_total=alto_total or h_arranque+r+.5
    for k in range(n+1):
        ss=s0+k*(luz+pilar)
        f.caja(ss,ss+pilar,0,alto_total,d0,d1,'muro',color)
    for k in range(n):
        centro=s0+pilar+r+k*(luz+pilar)
        for j in range(16):
            a=j*math.pi/16;b=(j+1)*math.pi/16
            sa=centro-r*math.cos(a);sb=centro-r*math.cos(b)
            ha=h_arranque+r*math.sin(a);hb=h_arranque+r*math.sin(b)
            f.c.poligono([f.punto(sa,ha,d0),f.punto(sb,hb,d0),
                           f.punto(sb,alto_total,d0),f.punto(sa,alto_total,d0)],
                          'muro',color,grosor=d1-d0,normal_extrusion=f.n)
        f.arco(centro,r,.13,h_arranque,d1,d1+.08,'moldura',color,segmentos=16)


def pavimentar(c,huella,rol='piedra',offset=.14,paso=5,color=None):
    """Pavimento interior sobre el terreno interpolado, con triángulos cortos."""
    from kit import altura_suelo
    from triangulacion_codex import triangular_huella
    def agregar(tri):
        a,b,d=tri
        pares=((a,b,d),(b,d,a),(d,a,b))
        aa,bb,cc=max(pares,key=lambda p:math.dist(p[0],p[1]))
        if math.dist(aa,bb)>paso:
            med=((aa[0]+bb[0])/2,(aa[1]+bb[1])/2)
            agregar((aa,med,cc));agregar((med,bb,cc))
        else:c.poligono([(x,y,altura_suelo(x,y)+offset) for x,y in tri],rol,color)
    for tri in triangular_huella(huella):agregar(tri)


def semaforo_esquina(nombre,f,ss,col):
    """Mástil amarillo y semáforo horizontal de tres luces, M061/131002."""
    from kit import Constructor,altura_suelo
    from mathutils import Vector
    c=Constructor(nombre);p=f.punto(ss,0,1.2);z=altura_suelo(p.x,p.y)
    c.cilindro(p.x,p.y,z,z+5.9,.065,'metal','#cda52d',lados=8)
    centro=Vector((p.x,p.y,z+5.85))+f.n*2
    c.caja_ejes(centro,f.n,f.u,f.z,4,.09,.09,'metal','#cda52d')
    centro=Vector((p.x,p.y,z+5.6))+f.n*3.6
    c.caja_ejes(centro,f.n,f.u,f.z,1.25,.26,.38,'hierro')
    for k in range(3):
        q=centro+f.n*((k-1)*.39)+f.u*.15
        c.esfera(q.x,q.y,q.z,.12,'vidrio','#779947' if k==2 else '#3c4039',segmentos=8)
    return c.objeto(col)


def rama(c,a,b,r0=.07,r1=.035,rol='tronco',color=None):
    """Rama inclinada y cónica; evita troncos paralelos bajo una misma copa."""
    import bmesh
    from mathutils import Vector,Matrix
    a,b=Vector(a),Vector(b);direccion=b-a
    if direccion.length<.001:return
    matriz=Matrix.Translation((a+b)/2)@direccion.to_track_quat('Z','Y').to_matrix().to_4x4()
    r=bmesh.ops.create_cone(c.bm,cap_ends=True,segments=7,radius1=r0,radius2=r1,
                          depth=direccion.length,matrix=matriz)
    c._pintar(r['verts'],rol,color)

def copa_fina(c,x,y,z,rx,ry,rz,semilla=0):
    """Racimos pequeños y unidos para el árbol grande de R0017, sin esferas lisas."""
    import random
    az=random.Random(semilla)
    for k in range(9):
        a=k*2.39996;rr=.68*math.sqrt(k/8)
        cx=x+rx*rr*math.cos(a);cy=y+ry*rr*math.sin(a);cz=z+rz*az.uniform(-.3,.3)
        aa,bb,cc=rx*.48,ry*.5,rz*.7
        for j in range(5):
            u=-math.pi/2+j*math.pi/5;v=u+math.pi/5
            for t in range(10):
                q=t*math.tau/10;r=(t+1)*math.tau/10
                def p(h,w):return (cx+aa*math.cos(h)*math.cos(w),cy+bb*math.cos(h)*math.sin(w),cz+cc*math.sin(h))
                pts=[p(u,q),p(u,r),p(v,r),p(v,q)]
                if j==0:pts=[pts[0],pts[2],pts[3]]
                if j==4:pts=[pts[0],pts[1],pts[2]]
                c.poligono(pts,'follaje',('#486337','#506d3b','#5a7540')[k%3])

def recorte_estricto(huella,margen=.035):
    """Revisa cada 25 cm los frentes propios junto a curvas y finales de eje.

    El recorte común muestrea cuatro puntos por arista. En franjas largas,
    un tramo corto de calle puede pasar entre muestras y dejar una cuña.
    Solo corta si un punto del polígono entra en el tramo finito de calle.
    """
    from kit import datos
    h=[tuple(p) for p in huella]
    for vuelta in range(2):
        for calle in datos.calles_reales():
            if not calle.get('recortar',True):continue
            w=calle['ancho']/2+margen
            for a,b in zip(calle['eje'],calle['eje'][1:]):
                # Un tramo finito lejano no puede cortar la huella. Evita
                # muestrear sus aristas contra todas las calles de la ciudad.
                if (max(p[0] for p in h)<min(a[0],b[0])-w or
                    min(p[0] for p in h)>max(a[0],b[0])+w or
                    max(p[1] for p in h)<min(a[1],b[1])-w or
                    min(p[1] for p in h)>max(a[1],b[1])+w):continue
                dx,dy=b[0]-a[0],b[1]-a[1];L=math.hypot(dx,dy)
                if L<.05:continue
                ux,uy=dx/L,dy/L;nx,ny=-uy,ux
                invade=False
                for p,q in zip(h,h[1:]+h[:1]):
                    n=max(1,math.ceil(math.dist(p,q)/.25))
                    for k in range(n+1):
                        x=p[0]+(q[0]-p[0])*k/n;y=p[1]+(q[1]-p[1])*k/n
                        t=(x-a[0])*ux+(y-a[1])*uy;d=(x-a[0])*nx+(y-a[1])*ny
                        if 0<=t<=L and abs(d)<w-.001:invade=True;break
                    if invade:break
                if not invade:continue
                signo=1 if sum((p[0]-a[0])*nx+(p[1]-a[1])*ny for p in h)>=0 else -1
                def d(p):return ((p[0]-a[0])*nx+(p[1]-a[1])*ny)*signo-w
                out=[]
                for p,q in zip(h,h[1:]+h[:1]):
                    dp,dq=d(p),d(q)
                    if dp>=0:out.append(p)
                    if (dp>=0)!=(dq>=0):
                        t=dp/(dp-dq);out.append((p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
                if len(out)<3:raise ValueError('Huella propia completamente dentro de una calle')
                h=out
    return h
