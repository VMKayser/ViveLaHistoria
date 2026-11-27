"""Huellas de limpieza: corredores finitos y separación de parcelas solapadas.
Cálculo 2D propio, sin modificar el reparto ni incorporar dependencias.
Conserva las huellas pequeñas al recortar el volumen genérico mayor.
"""
import math
from triangulacion_codex import triangular_huella
from pavimentos_codex import _partir,_area


def caja(h):return min(p[0] for p in h),min(p[1] for p in h),max(p[0] for p in h),max(p[1] for p in h)
def coinciden(a,b):return not(a[2]<b[0] or b[2]<a[0] or a[3]<b[1] or b[3]<a[1])


def diferencia_convexa(p,recorte):
    resto=p;fuera=[]
    if not coinciden(caja(p),caja(recorte)):return [p]
    if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(recorte,recorte[1:]+recorte[:1]))<0:recorte=list(reversed(recorte))
    for a,b in zip(recorte,recorte[1:]+recorte[:1]):
        if len(resto)<3:break
        resto,exterior=_partir(resto,lambda p:(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]))
        if len(exterior)>2 and _area(exterior)>1e-8:fuera.append(exterior)
    return fuera


def anillos_de_piezas(piezas):
    """Cancela aristas internas, partiendo primero las uniones en T."""
    def key(p):return round(p[0],6),round(p[1],6)
    puntos={key(p) for h in piezas for p in h};aristas=set()
    for h in piezas:
        if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(h,h[1:]+h[:1]))<0:h=list(reversed(h))
        for p,q in zip(h,h[1:]+h[:1]):
            p,q=key(p),key(q);dx,dy=q[0]-p[0],q[1]-p[1];ll=dx*dx+dy*dy
            if ll<1e-12:continue
            entre=[]
            for r in puntos:
                t=((r[0]-p[0])*dx+(r[1]-p[1])*dy)/ll
                if -1e-7<=t<=1+1e-7 and abs(dx*(r[1]-p[1])-dy*(r[0]-p[0]))<2e-6*math.sqrt(ll):entre.append((t,r))
            entre.sort()
            for (_,a),(_,b) in zip(entre,entre[1:]):
                if a==b:continue
                if (b,a) in aristas:aristas.remove((b,a))
                else:aristas.add((a,b))
    anillos=[]
    while aristas:
        a,b=min(aristas);inicio=a;h=[a];aristas.remove((a,b));anterior=a;actual=b
        for _ in range(len(puntos)*3+3):
            if actual==inicio:break
            h.append(actual);opciones=[q for p,q in aristas if p==actual]
            if not opciones:raise ValueError('Contorno abierto después del recorte')
            # En contactos puntuales, continuar por el límite de la misma región.
            ang=math.atan2(actual[1]-anterior[1],actual[0]-anterior[0])
            siguiente=max(opciones,key=lambda q:(math.atan2(q[1]-actual[1],q[0]-actual[0])-ang)%(2*math.pi))
            aristas.remove((actual,siguiente));anterior,actual=actual,siguiente
        else:raise ValueError('Contorno sin cerrar')
        if len(h)>2 and _area(h)>1e-7:anillos.append(h)
    return anillos


_CACHE={}
def plan_parcela(e,datos=None):
    if datos is None:
        from kit import datos
    # datos ya aplica el recorte común; completar los tramos interiores que
    # no alcanzaban las muestras de las aristas del lienzo.
    exclusiones=e.get('excluir_huellas',[])
    clave=(e['id'],tuple(map(tuple,e['huella'])),tuple(tuple(map(tuple,h)) for h in exclusiones))
    if clave in _CACHE:return _CACHE[clave]
    h=[tuple(p) for p in e['huella']];piezas=[list(t) for t in triangular_huella(h)]
    for calle in datos.calles_reales():
        if not calle.get('recortar',True):continue
        w=calle['ancho']/2+.035
        for a,b in zip(calle['eje'],calle['eje'][1:]):
            L=math.dist(a,b)
            if L<.1:continue
            ux,uy=(b[0]-a[0])/L,(b[1]-a[1])/L;nx,ny=-uy,ux
            rect=[(a[0]-ux*.03+nx*w,a[1]-uy*.03+ny*w),(a[0]-ux*.03-nx*w,a[1]-uy*.03-ny*w),
                  (b[0]+ux*.03-nx*w,b[1]+uy*.03-ny*w),(b[0]+ux*.03+nx*w,b[1]+uy*.03+ny*w)]
            if coinciden(caja(h),caja(rect)):piezas=[q for p in piezas for q in diferencia_convexa(p,rect)]
    for reservada in exclusiones:
        for tri in triangular_huella(reservada):piezas=[q for p in piezas for q in diferencia_convexa(p,list(tri))]
    prioridad=(_area(h),e['id']);vecinos=[]
    for m in datos.reparto()['manzanas']:
        for otro in m['edificios']:
            if otro['id']==e['id']:continue
            oh=datos.recortar_a_calles(otro.get('huella_lienzo',otro['huella']))
            if not oh:continue
            if (_area(oh),otro['id'])>=prioridad or not coinciden(caja(h),caja(oh)):continue
            antes=sum(_area(p) for p in piezas)
            for tri in triangular_huella(oh):piezas=[q for p in piezas for q in diferencia_convexa(p,list(tri))]
            if antes-sum(_area(p) for p in piezas)>1e-5:vecinos.append(otro['id'])
    piezas=[p for p in piezas if len(p)>2 and _area(p)>1e-7]
    anillos=anillos_de_piezas(piezas)
    exteriores=[p for p in anillos if sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(p,p[1:]+p[:1]))>0]
    assert exteriores,('Parcela eliminada',e['id'])
    plan={'anillos':anillos,'exteriores':exteriores,'piezas':piezas,'vecinos':vecinos,'principal':max(exteriores,key=_area)}
    _CACHE[clave]=plan
    return plan


def volumen_colonial(c,plan,z0,z1,color_muro,color_teja,altura_cubierta_max=1.85):
    """Envolvente cerrada: paredes, suelo y cubierta sin tapas internas."""
    from kit import lados
    from casas_codex import _cortar
    h=plan['principal'];l=max(lados(h),key=lambda l:l['largo']);a=l['a'];n=l['normal']
    vv=[(p[0]-a[0])*n[0]+(p[1]-a[1])*n[1] for ring in plan['anillos'] for p in ring];v0,v1=min(vv),max(vv);vm=(v0+v1)/2
    H=min(altura_cubierta_max,max(.45,(v1-v0)*.18))
    def coord(p):return (p[0]-a[0])*n[0]+(p[1]-a[1])*n[1]
    def alto(p):return z1+.025+H*(1-abs(coord(p)-vm)/max(.01,(v1-v0)/2))
    for ring in plan['anillos']:
        for p,q in zip(ring,ring[1:]+ring[:1]):
            puntos=[p]
            if (coord(p)-vm)*(coord(q)-vm)<-1e-10:
                t=(vm-coord(p))/(coord(q)-coord(p));puntos.append((p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t))
            puntos.append(q)
            for a0,b0 in zip(puntos,puntos[1:]):
                c.poligono([(a0[0],a0[1],z0),(b0[0],b0[1],z0),(b0[0],b0[1],alto(b0)),(a0[0],a0[1],alto(a0))],'muro',color_muro)
    for p in plan['piezas']:
        c.poligono([(x,y,z0) for x,y in reversed(p)],'muro',color_muro)
        for signo in (-1,1):
            mitad=_cortar(p,a,n,vm,signo)
            if len(mitad)>2 and _area(mitad)>1e-8:c.poligono([(x,y,alto((x,y))) for x,y in mitad],'teja',color_teja)


def recortar_detalles(c,e,datos):
    """Corta las molduras en medianeras reales, conservando su material y Z.

    No basta recortar el cuerpo: una cornisa o una pilastra terminal también
    puede atravesar la casa contigua. Las caras conservadas acaban justo en
    el límite; los vuelos hacia la calle no se recortan.
    """
    import bmesh
    caras=list(c.bm.faces)
    if not caras:return
    puntos=[v.co for v in c.bm.verts];bb=caja(puntos)
    recortes=list(e.get('excluir_huellas',[]))
    for m in datos.reparto()['manzanas']:
        for otro in m['edificios']:
            if otro['id']==e['id']:continue
            h=datos.recortar_a_calles(otro.get('huella_lienzo',otro['huella']))
            if not h or not coinciden(bb,caja(h)):continue
            # Aplicar la misma partición de lotes que a los cuerpos.
            plan=plan_parcela(dict(otro,huella=h),datos)
            recortes.extend(plan['piezas'])
    if not recortes:return
    def partir3d(h,a,b):
        dentro=[];fuera=[]
        def d(p):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
        for p,q in zip(h,h[1:]+h[:1]):
            dp,dq=d(p),d(q)
            (dentro if dp>=0 else fuera).append(p)
            if (dp>=0)!=(dq>=0):
                t=dp/(dp-dq);r=tuple(p[k]+t*(q[k]-p[k]) for k in range(3))
                dentro.append(r);fuera.append(r)
        return dentro,fuera
    nuevas=[]
    for f in caras:
        partes=[[tuple(v.co) for v in f.verts]]
        for h in recortes:
            fuera=[]
            if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(h,h[1:]+h[:1]))<0:h=list(reversed(h))
            for p in partes:
                if not coinciden(caja(p),caja(h)):fuera.append(p);continue
                resto=p
                for a,b in zip(h,h[1:]+h[:1]):
                    if len(resto)<3:break
                    resto,q=partir3d(resto,a,b)
                    if len(q)>2:fuera.append(q)
            partes=fuera
        nuevas.extend((p,f.material_index) for p in partes)
    bmesh.ops.delete(c.bm,geom=caras,context='FACES')
    for p,mat in nuevas:
        # Quitar duplicados consecutivos producidos al pasar por un vértice.
        limpia=[]
        for v in p:
            if not limpia or math.dist(v,limpia[-1])>1e-6:limpia.append(v)
        if len(limpia)>2 and math.dist(limpia[0],limpia[-1])<1e-6:limpia.pop()
        if len(limpia)<3:continue
        vs=[c.bm.verts.new(v) for v in limpia]
        cara=c.bm.faces.new(vs)
        if cara.calc_area()<1e-9:c.bm.faces.remove(cara)
        else:cara.material_index=mat


def lucernario_si_ciego(c,detalles):
    """Luz cenital para una casa encerrada entre medianeras, sin vanos falsos.

    Si el recorte elimina todos los vidrios de fachada, abre un lucernario
    rectangular real en un faldón. Sustituye la teja por vidrio en esa
    abertura; el marco descansa en sus cuatro bordes.
    """
    activos={detalles.mats[f.material_index].split('__')[0] for f in detalles.bm.faces}
    if {'vidrio','marco_ventana','hierro'}<=activos and activos&{'madera','metal'}:return
    import bmesh
    from mathutils import Vector
    from varillas_codex import rama
    tejas={i for i,n in enumerate(c.mats) if n.startswith('teja')}
    cara=max((f for f in c.bm.faces if f.material_index in tejas),key=lambda f:f.calc_area())
    pp=[v.co.copy() for v in cara.verts];cara.normal_update();normal=cara.normal.copy()
    centro=sum(pp,Vector())/len(pp);u=(pp[1]-pp[0]);u.z=0;u.normalize();v=Vector((-u.y,u.x,0))
    huella=[tuple(p[:2]) for p in pp]
    if sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(huella,huella[1:]+huella[:1]))<0:huella.reverse()
    for escala in (1,.8,.6,.4,.25,.1):
        rect=[centro+u*(x*.5*escala)+v*(y*.4*escala) for x,y in ((-1,-1),(1,-1),(1,1),(-1,1))]
        if all(all((b[0]-a[0])*(p.y-a[1])-(b[1]-a[1])*(p.x-a[0])>=1e-5 for a,b in zip(huella,huella[1:]+huella[:1])) for p in rect):break
    else:
        # tras el ensanche de calles (2026-11-24) algunos faldones recortados quedan sin sitio: sin lucernario, sin abortar
        print('[codex] no cabe lucernario en',c.nombre,'- se omite');return
    def z(p):return pp[0].z-(normal.x*(p[0]-pp[0].x)+normal.y*(p[1]-pp[0].y))/normal.z
    abertura=[tuple(p[:2]) for p in rect];mat=cara.material_index
    bmesh.ops.delete(c.bm,geom=[cara],context='FACES')
    for h in diferencia_convexa(huella,abertura):
        vs=c.poligono([(x,y,z((x,y))) for x,y in h],'teja')
        for f in {f for vertex in vs for f in vertex.link_faces}:f.material_index=mat
    borde=[Vector((x,y,z((x,y)))) for x,y in abertura]
    c.poligono(borde,'vidrio','#91a49e')
    for a,b in zip(borde,borde[1:]+borde[:1]):
        rama(detalles,a-normal*.025,b-normal*.025,.035,.035,'madera','#79553a')
        rama(detalles,a+normal*.015,b+normal*.015,.015,.015,'marco_ventana','#6a746d')

    # Reja de protección apoyada en los marcos, dentro del lucernario.
    for t in (.25,.5,.75):
        a=borde[0].lerp(borde[1],t)+normal*.035
        b=borde[3].lerp(borde[2],t)+normal*.035
        rama(detalles,a,b,.015,.015,'hierro','#3b473e')
