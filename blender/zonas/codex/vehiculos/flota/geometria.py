"""Piezas geométricas compartidas; cada diseño conserva sus propios perfiles."""
import math
from collections import defaultdict
import bmesh
import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from acabados_bronco import contorno_redondeado


def interpolar(filas, x, columna):
    if x <= filas[0][0]:
        return filas[0][columna]
    for a, b in zip(filas, filas[1:]):
        if x <= b[0]:
            t = (x-a[0])/(b[0]-a[0])
            return a[columna]*(1-t)+b[columna]*t
    return filas[-1][columna]


class Taller:
    def __init__(self, identificador, datos, materiales):
        self.id, self.d, self.m = identificador, datos, materiales
        self.g = {}
        self.g['raiz'] = self.vacio(identificador)
        self.g['raiz']['unidades'] = 'metros'
        self.g['raiz']['frente_blender'] = '+X'
        self.g['raiz']['origen'] = 'suelo, centro longitudinal del cuerpo'
        for nombre in ['carroceria', 'cristales', 'interior', 'decoracion']:
            self.g[nombre] = self.vacio(nombre, padre=self.g['raiz'])

    def vacio(self, nombre, posicion=(0, 0, 0), padre=None):
        o = bpy.data.objects.new(nombre, None)
        bpy.context.collection.objects.link(o)
        o.location, o.parent = posicion, padre
        return o

    def asignar(self, o, mat, grupo='carroceria'):
        if mat:
            o.data.materials.append(self.m.get(mat, mat) if isinstance(mat, str) else mat)
        bpy.context.view_layer.update()
        o.parent = self.g[grupo]
        o.matrix_parent_inverse = o.parent.matrix_world.inverted()
        return o

    def malla(self, nombre, vertices, caras, mat, grupo='carroceria', suave=False):
        me = bpy.data.meshes.new(nombre)
        me.from_pydata(vertices, [], caras)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = suave
        o = bpy.data.objects.new(nombre, me)
        bpy.context.collection.objects.link(o)
        return self.asignar(o, mat, grupo)

    def caja(self, nombre, centro, medidas, mat, bisel=.02, grupo='carroceria'):
        bpy.ops.mesh.primitive_cube_add(size=1, location=centro)
        o = bpy.context.object
        o.name, o.dimensions = nombre, medidas
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if bisel:
            mod = o.modifiers.new('Encuentros redondeados', 'BEVEL')
            mod.width, mod.segments = bisel, 3
            bpy.ops.object.modifier_apply(modifier=mod.name)
            mod = o.modifiers.new('Normales de chapa', 'WEIGHTED_NORMAL')
            bpy.ops.object.modifier_apply(modifier=mod.name)
        return self.asignar(o, mat, grupo)

    def cilindro(self, nombre, centro, radio, fondo, mat, eje='Y', lados=32, grupo='carroceria'):
        bpy.ops.mesh.primitive_cylinder_add(vertices=lados, radius=radio, depth=fondo, location=centro)
        o = bpy.context.object
        o.name = nombre
        if eje == 'Y':
            o.rotation_euler.x = math.pi/2
        elif eje == 'X':
            o.rotation_euler.y = math.pi/2
        for p in o.data.polygons:
            p.use_smooth = len(p.vertices) == 4
        return self.asignar(o, mat, grupo)

    def tubo(self, nombre, puntos, radio, mat, grupo='decoracion', cerrado=False):
        cu = bpy.data.curves.new(nombre, 'CURVE')
        cu.dimensions = '3D'
        cu.resolution_u, cu.bevel_depth, cu.bevel_resolution = 1, radio, 2
        cu.use_fill_caps = True
        sp = cu.splines.new('POLY')
        sp.points.add(len(puntos)-1)
        for p, co in zip(sp.points, puntos):
            p.co = (*co, 1)
        sp.use_cyclic_u = cerrado
        o = bpy.data.objects.new(nombre, cu)
        bpy.context.collection.objects.link(o)
        return self.asignar(o, mat, grupo)

    def panel(self, nombre, puntos, mat, grupo='carroceria'):
        vs = [Vector(p) for p in puntos]
        indices = {tuple(p): i for i, p in enumerate(vs)}
        caras = [[v if isinstance(v, int) else indices[tuple(v)] for v in tri]
                 for tri in tessellate_polygon([vs])]
        return self.malla(nombre, puntos, caras, mat, grupo)

    def cortar(self, objeto, cortador):
        bpy.context.view_layer.objects.active = objeto
        mod = objeto.modifiers.new('Hueco real', 'BOOLEAN')
        mod.operation, mod.solver, mod.object = 'DIFFERENCE', 'EXACT', cortador
        bpy.ops.object.modifier_apply(modifier=mod.name)
        bpy.data.objects.remove(cortador, do_unlink=True)

    def ancho(self, x):
        return interpolar(self.d['secciones'], x, 1)

    def cintura(self, x):
        return interpolar(self.d['secciones'], x, 2)

    def lado(self, x, z, s, salida=0):
        """Cabina ligeramente inclinada hacia dentro; base enlazada con cintura."""
        a = self.ancho(x)*.94
        t = max(0, min(1, (z-self.cintura(x))/(self.d['alto']-.04-self.cintura(x))))
        return (x, s*(a*(1-t)+self.d['ancho_techo']*t+salida), z)

    def chapa_y(self, x, z, s, salida=.003):
        c, b = self.cintura(x), self.d['bajo']
        perfil = [[b,.90],[b+.04,.98],[b+.10,.98],[c-.38,.965],[c-.25,.995],[c-.10,1],[c-.035,.98],[c,.94]]
        perfil.sort()
        return s*(self.ancho(x)*interpolar(perfil, z, 1)+salida)

    def torno(self, nombre, perfil, x, y, z, s, mat, grupo, segmentos=64, cerrado=False):
        # UV cilíndrica por esquina; vértices de la costura geométrica soldados.
        vs = [(x+r*math.cos(math.tau*j/segmentos-math.pi/2), y+s*d,
               z+r*math.sin(math.tau*j/segmentos-math.pi/2))
              for r,d in perfil for j in range(segmentos+1)]
        n = segmentos+1
        caras = [(i*n+j,i*n+j+1,((i+1)%len(perfil))*n+j+1,((i+1)%len(perfil))*n+j)
                 for i in range(len(perfil) if cerrado else len(perfil)-1) for j in range(segmentos)]
        o = self.malla(nombre, vs, caras, mat, grupo, True)
        uv = o.data.uv_layers.new(name='UVMap')
        for p in o.data.polygons:
            for loop in p.loop_indices:
                i,j = divmod(o.data.loops[loop].vertex_index,n)
                uv.data[loop].uv = (j/segmentos*8,i/max(1,len(perfil)-1)*2)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(o.data)
        bm.free()
        return o

    def consolidar(self):
        curvas = [o for o in bpy.context.scene.objects if o.type == 'CURVE']
        bpy.ops.object.select_all(action='DESELECT')
        for o in curvas:
            o.select_set(True)
        if curvas:
            bpy.context.view_layer.objects.active = curvas[0]
            bpy.ops.object.convert(target='MESH')
        lotes = defaultdict(list)
        for o in bpy.context.scene.objects:
            if o.type == 'MESH':
                # Los booleanos pueden añadir slots vacíos del cortador. Cada
                # pieza de este taller tiene un material deliberado único.
                mat = next(m for m in o.data.materials if m is not None)
                o.data.materials.clear()
                o.data.materials.append(mat)
                for p in o.data.polygons:
                    p.material_index = 0
                lotes[(o.parent.name,mat.name)].append(o)
        for (padre, mat), obs in lotes.items():
            bpy.ops.object.select_all(action='DESELECT')
            for o in obs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = obs[0]
            if len(obs)>1:
                bpy.ops.object.join()
            o = obs[0]
            o.name = padre+'__'+mat
            bm = bmesh.new()
            bm.from_mesh(o.data)
            bmesh.ops.dissolve_degenerate(bm, dist=1e-6, edges=list(bm.edges))
            bmesh.ops.triangulate(bm, faces=list(bm.faces))
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_area()<1e-11], context='FACES')
            for e in bm.edges:
                if len(e.link_faces)==2 and e.calc_face_angle()>math.radians(50):
                    e.smooth=False
            bm.to_mesh(o.data)
            bm.free()
            if mat != self.m['neumatico'].name:
                for uv in list(o.data.uv_layers):
                    o.data.uv_layers.remove(uv)


def cuerpo(t):
    d=t.d
    filas=d['secciones']
    xs = sorted(set([p[0] for p in filas]+[filas[0][0]+(filas[-1][0]-filas[0][0])*i/65 for i in range(66)]))
    vs=[]
    for x in xs:
        w,c,b=t.ancho(x),t.cintura(x),d['bajo']
        mitad=[(0,c+.035),(.65*w,c+.026),(.88*w,c+.012),(.94*w,c),(.98*w,c-.035),
               (w,c-.10),(.995*w,c-.25),(.965*w,c-.38),(.98*w,b+.10),(.98*w,b+.04),(.90*w,b),(0,b)]
        anillo=mitad+ [(-y,z) for y,z in reversed(mitad[1:-1])]
        vs.extend((x,y,z) for y,z in anillo)
    n=len(anillo)
    caras=[tuple(range(n-1,-1,-1))]
    caras += [(i*n+j,i*n+(j+1)%n,(i+1)*n+(j+1)%n,(i+1)*n+j) for i in range(len(xs)-1) for j in range(n)]
    caras.append(tuple((len(xs)-1)*n+j for j in range(n)))
    o=t.malla('Chapa con hombros curvos y capó',vs,caras,'pintura',suave=True)
    # Cabina hueca: piso bajo la línea de cristales. Se evita un bloque macizo
    # detrás de la ventana; quedan umbrales y laterales con grosor real.
    a,b=d['luneta'][0][0]+.10,d['parabrisas'][0][0]-.16
    t.cortar(o,t.caja('Cortador habitáculo',((a+b)/2,0,1.8),(b-a,(d['ancho']/2-.14)*2,2.1),None,0))
    if d['tipo']=='pickup':
        a,b=filas[0][0]+.10,d['caja_hasta']
        t.cortar(o,t.caja('Cortador caja abierta',((a+b)/2,0,1.8),(b-a,d['ancho']-.24,2.0),None,.035))
        t.caja('Fondo de la caja',((a+b)/2,0,.87),(b-a,d['ancho']-.25,.07),'oscuro',.015,'interior')
        for y in [-.6,-.4,-.2,0,.2,.4,.6]:
            t.caja('Nervadura piso caja',((a+b)/2,y,.913),(b-a-.07,.023,.016),'oscuro',.007,'interior')
        for s in [-1,1]:
            t.caja('Protector borde de caja',((a+b)/2,s*(d['ancho']/2-.065),1.285 if d['id']!='toyota_roja' else 1.235),
                   (b-a+.12,.085,.045),'oscuro',.018)
        if d.get('caja_cubierta'):
            t.caja('Cubierta de caja',((a+b)/2,0,1.275),(b-a+.04,d['ancho']-.18,.055),'oscuro',.022)
    # Los cilindros atraviesan ambas caras: huecos auténticos y coherentes.
    for x in d['ejes']:
        t.cortar(o,t.cilindro('Cortador paso rueda',(x,0,d['radio_rueda']),d['radio_rueda']+.055,d['ancho']+.5,None,lados=64))
    for x in d['ejes']:
        for s in [-1,1]:
            r=d['radio_rueda']+.057
            vs=[]
            ancho=.07 if d.get('moldura_arcos') else .042
            for j in range(4):
                radio=r+ancho*j/3
                for i in range(41):
                    a=math.pi*i/40
                    xx,zz=x+radio*math.cos(a),d['radio_rueda']+radio*math.sin(a)
                    yy=t.chapa_y(xx,zz,s,.009+.028*math.sin(math.pi*j/3))
                    vs.append((xx,yy,zz))
            t.malla('Guardabarros esculpido',vs,[(j*41+i,j*41+i+1,(j+1)*41+i+1,(j+1)*41+i) for j in range(3) for i in range(40)],d.get('moldura_arcos','pintura'),suave=True)
            t.caja('Faldón guardabarros',(x-d['radio_rueda']-.07,s*d['semivia_ruedas'],d['bajo']-.08),(.045,d['ancho_rueda'],.25),'oscuro',.014,'interior')
    t.caja('Bajos y largueros',(0,0,d['bajo']+.04),(d['largo']-.4,1.0,.15),'oscuro',.045,'interior')


def cabina(t):
    d=t.d
    # Techo con sección arqueada: no una caja con chaflanes.
    vs=[]
    xs=[d['techo'][0][0]+(d['techo'][-1][0]-d['techo'][0][0])*i/24 for i in range(25)]
    for x in xs:
        z=interpolar(d['techo'],x,1)
        for j in range(25):
            u=-1+2*j/24
            vs.append((x,d['ancho_techo']*u,z+.025*(1-u*u)))
    o=t.malla('Techo arqueado',vs,[(i*25+j,i*25+j+1,(i+1)*25+j+1,(i+1)*25+j) for i in range(24) for j in range(24)],'pintura',suave=True)
    mod=o.modifiers.new('Espesor techo','SOLIDIFY')
    mod.thickness=.025
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_apply(modifier=mod.name)
    for s in [-1,1]:
        t.tubo('Encuentro continuo techo y montantes',[(x,s*d['ancho_techo'],interpolar(d['techo'],x,1)) for x in xs],.022,'pintura')
        for k,celda in enumerate(d['ventanas']):
            cx=sum(p[0] for p in celda)/len(celda)
            cz=sum(p[1] for p in celda)/len(celda)
            # Marco ancho de chapa, burlete fino y vidrio ligeramente retraído.
            interno=[(cx+(x-cx)*.86,cz+(z-cz)*.81) for x,z in celda]
            fuera=[t.lado(x,z,s) for x,z in celda]
            dentro=[t.lado(x,z,s,.002) for x,z in interno]
            t.malla('Pilares y marco de ventana',fuera+dentro,[(i,(i+1)%4,(i+1)%4+4,i+4) for i in range(4)],'pintura')
            # Cubrir el rincón entre el hueco rectangular y el vidrio redondeado.
            redondo=contorno_redondeado(interno,.028,5)
            cont=[t.lado(x,z,s,.003) for x,z in redondo]
            for i in range(4):
                tramo=cont[i*6:(i+1)*6]
                t.panel('Esquina de marco redondeada',[dentro[i]]+tramo,'pintura')
            dentro=cont
            t.tubo('Burlete continuo',dentro,.012,'oscuro',cerrado=True)
            t.panel('Cristal lateral '+str(k),[t.lado(x,z,s,-.006) for x,z in redondo],'vidrio','cristales')
        # Juntas de puerta siguen la chapa y se detienen antes del arco.
        for a,b in d['puertas']:
            z0=d['bajo']+.12
            for x in [a,b]:
                puntos=[]
                for j in range(16):
                    z=z0+(t.cintura(x)-z0)*j/15
                    if all((x-e)**2+(z-d['radio_rueda'])**2>(d['radio_rueda']+.07)**2 for e in d['ejes']):
                        puntos.append((x,t.chapa_y(x,z,s),z))
                if len(puntos)>1:
                    t.tubo('Junta de puerta',puntos,.0035,'oscuro')
            x=a+.18
            z=t.cintura(x)-.115
            t.caja('Cazoleta de manija',(x,t.chapa_y(x,z,s,.006),z),(.19,.026,.066),'oscuro',.025,'decoracion')
            t.caja('Manija',(x,t.chapa_y(x,z,s,.023),z+.004),(.14,.028,.027),'cromo' if d['id'] in ['montero_sport_blanca','toyota_roja'] else 'oscuro',.012,'decoracion')
        # Espejos con brazo y cara reflectante independiente.
        x,z=d['espejo_x'],d['cintura']+.11
        y=d['ancho']/2
        t.tubo('Brazo espejo',[(x,s*(y-.04),z-.08),(x-.06,s*(y+.12),z-.02)],.025,'oscuro')
        t.caja('Carcasa espejo',(x-.05,s*(y+.17),z),(.23,.17,.15),'oscuro',.055,'decoracion')
        t.caja('Cristal espejo',(x-.172,s*(y+.17),z),(.009,.12,.105),'cromo',.023,'decoracion')
    for nombre,filas,signo in [('Parabrisas',d['parabrisas'],1),('Luneta',d['luneta'],-1)]:
        def punto(u,v):
            a,b=filas
            x=a[0]*(1-v)+b[0]*v+signo*.022*(1-u*u)
            z=a[1]*(1-v)+b[1]*v+.009*(1-u*u)
            return (x,u*(a[2]*(1-v)+b[2]*v),z)
        vs=[punto(-1+2*j/24,i/12) for i in range(13) for j in range(25)]
        caras=[]
        for i in range(12):
            for j in range(24):
                # El perímetro es chapa que cierra A/C, techo y cintura.
                if i in [0,11] or j in [0,23]:
                    caras.append((i*25+j,i*25+j+1,(i+1)*25+j+1,(i+1)*25+j))
        t.malla(nombre+' marco de chapa',vs,caras,'pintura',suave=True)
        caras=[(i*25+j,i*25+j+1,(i+1)*25+j+1,(i+1)*25+j) for i in range(1,11) for j in range(1,23)]
        t.malla(nombre+' vidrio curvo',vs,caras,'vidrio','cristales',True)
        contorno=[punto(-1+2*j/24,1/12) for j in range(1,24)]
        contorno += [punto(22/24,i/12) for i in range(2,12)]
        contorno += [punto(-1+2*j/24,11/12) for j in range(22,0,-1)]
        contorno += [punto(-22/24,i/12) for i in range(10,1,-1)]
        t.tubo(nombre+' junta de goma',contorno,.009,'oscuro',cerrado=True)
        if nombre=='Parabrisas':
            for y in [-.40,.27]:
                a=punto(y/filas[0][2],.09)
                b=punto((y+.24)/filas[0][2],.16)
                t.tubo('Limpiaparabrisas',[(a[0]+.016,a[1],a[2]),(b[0]+.016,b[1],b[2])],.010,'oscuro')
    if d['barras_techo']:
        for s in [-1,1]:
            a,b=d['techo'][0][0]+.14,d['techo'][-1][0]-.12
            z=d['alto']+.018
            t.tubo('Barra longitudinal de techo',[(a,s*.60,z-.065),(a+.13,s*.60,z),(b-.12,s*.60,z),(b,s*.60,z-.06)],.022,'oscuro')


def interior(t):
    d=t.d
    c=d['cintura']
    for x in [d['parabrisas'][0][0]-.65,d['luneta'][0][0]+.70]:
        for y in [-.40,.40]:
            t.caja('Banqueta',(x,y,c-.27),(.44,.45,.13),'tapizado',.055,'interior')
            respaldo=t.caja('Respaldo',(x-.20,y,c-.07),(.115,.43,.47),'tapizado',.055,'interior')
            respaldo.rotation_euler.y=-.10
            t.caja('Apoyacabezas',(x-.22,y,c+.23),(.12,.24,.15),'tapizado',.045,'interior')
    x=d['parabrisas'][0][0]-.18
    t.caja('Tablero',(x,0,c+.015),(.32,d['ancho']-.36,.16),'oscuro',.055,'interior')
    cx=x-.27
    puntos=[(cx,.37+.16*math.cos(math.tau*i/32),c+.16+.16*math.sin(math.tau*i/32)) for i in range(32)]
    t.tubo('Volante',puntos,.016,'oscuro','interior',True)
    for i in range(3):
        a=math.tau*i/3
        t.tubo('Radio volante',[(cx,.37,c+.16),(cx,.37+.15*math.cos(a),c+.16+.15*math.sin(a))],.013,'oscuro','interior')


def ruedas(t):
    d=t.d
    r,w,ra=d['radio_rueda'],d['ancho_rueda']/2,d['radio_aro']
    perfil=[(ra*.96,-w*.82),(r*.72,-w*1.02),(r*.88,-w*1.02),(r*.97,-w*.84),(r,-w*.64),
            (r,-w*.38),(r-.005,-w*.31),(r,-w*.24),(r,-w*.08),(r-.005,0),(r,w*.08),
            (r,w*.24),(r-.005,w*.31),(r,w*.38),(r,w*.64),(r*.97,w*.84),(r*.88,w*1.02),(r*.72,w*1.02),(ra*.96,w*.82)]
    def rueda(x,y,z,s,grupo):
        t.torno('Neumático perfil radial',perfil,x,y,z,s,'neumatico',grupo)
        labio=[(ra*.92,w*.93),(ra,w*1.02),(ra*1.025,w*.95),(ra*1.025,-w*.85),(ra*.96,-w*.85)]
        t.torno('Aro con garganta y labio',labio,x,y,z,s,'llanta',grupo,cerrado=True)
        t.cilindro('Tambor de freno',(x,y,z),ra*.82,w*1.2,'oscuro',grupo=grupo)
        if d['aro_acero']:
            p=[(ra*.25,w*1.04),(ra*.42,w*.98),(ra*.72,w*.69),(ra*.91,w*.86),(ra*.94,w*.82),(ra*.70,w*.60),(ra*.25,w*.94)]
            aro=t.torno('Plato cóncavo de acero',p,x,y,z,s,'llanta',grupo,cerrado=True)
            for i in range(d['radios_aro']):
                a=math.tau*i/d['radios_aro']
                t.cortar(aro,t.cilindro('Perforación de ventilación',(x+ra*.67*math.cos(a),y+s*w*.85,z+ra*.67*math.sin(a)),ra*.12,w*1.5,None,lados=16,grupo=grupo))
        else:
            for i in range(d['radios_aro']):
                a=math.tau*i/d['radios_aro']
                # Radio inclinado y ahusado: agujeros entre radios son reales.
                p=[(ra*.20,-ra*.10),(ra*.91,-ra*.07),(ra*.95,ra*.03),(ra*.28,ra*.16)]
                vs=[]
                for profundidad in [w*.64,w*.97]:
                    vs.extend((x+u*math.cos(a)-v*math.sin(a),y+s*profundidad,z+u*math.sin(a)+v*math.cos(a)) for u,v in p)
                t.malla('Radio de aleación',vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],'llanta',grupo)
        t.cilindro('Centro de rueda',(x,y+s*w*1.04,z),ra*.25,.025,'llanta',grupo=grupo)
        t.cilindro('Tapón del buje',(x,y+s*(w*1.04+.016),z),ra*.12,.012,'oscuro',grupo=grupo)
        for i in range(5 if d['radios_aro']==5 else 6):
            a=math.tau*i/(5 if d['radios_aro']==5 else 6)
            t.cilindro('Tuerca',(x+ra*.32*math.cos(a),y+s*w*.99,z+ra*.32*math.sin(a)),.010,.016,'cromo',lados=6,grupo=grupo)
        # Marcas transversales de rodadura en el hombro, no una textura pintada.
        for i in range(48):
            a=math.tau*i/48
            for lado in [-1,1]:
                puntos=[(x+(r+.0008)*math.cos(a+.012*j),y+s*lado*w*(.42+.17*j),z+(r+.0008)*math.sin(a+.012*j)) for j in range(3)]
                t.tubo('Surco transversal',puntos,.0025,'oscuro',grupo)
    for ie,x in enumerate(d['ejes']):
        for s in [-1,1]:
            nombre=f"rueda_{'trasera' if ie==0 else 'delantera'}_{'derecha' if s==-1 else 'izquierda'}"
            y=s*d['semivia_ruedas']
            if ie:
                dn=nombre.replace('rueda_','direccion_')
                t.g[dn]=t.vacio(dn,(x,y,r),t.g['raiz'])
                t.g[nombre]=t.vacio(nombre,padre=t.g[dn])
            else:
                t.g[nombre]=t.vacio(nombre,(x,y,r),t.g['raiz'])
            rueda(x,y,r,s,nombre)
    if d.get('repuesto'):
        # Reutilizar el diseño de rueda y transformarlo a eje longitudinal fijo.
        nombre='repuesto_fijo'
        t.g[nombre]=t.vacio(nombre,padre=t.g['raiz'])
        rueda(0,0,0,1,nombre)
        bpy.context.view_layer.update()
        t.g[nombre].rotation_euler.z=math.pi/2
        t.g[nombre].location=(-d['largo']/2-.08,0,.99)
