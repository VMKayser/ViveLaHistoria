"""Modelo independiente desde disenos.json, con GLB, Blender, ficha y estudio.

blender -b -t 2 -P blender/zonas/codex/vehiculos/flota/construir.py -- vagoneta_blanca [--sin-render] [--vistas=perspectiva,lateral]
"""
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Vector

AQUI=Path(__file__).resolve().parent
VEHICULOS=AQUI.parent
RAIZ=AQUI.parents[4]
sys.path[:0]=[str(AQUI),str(VEHICULOS),str(RAIZ/'blender/kit')]
from paleta import material
from geometria import Taller, cuerpo, cabina, interior, ruedas
from detalles import frente, trasera, accesorios
from rig_bronco import preparar_movimiento

SALIDA=RAIZ/'web/public/models/ciudad/codex/vehiculos/flota'
REVISION=RAIZ/'revisiones/codex/flota'


def materiales(d):
    m={}
    for nombre,rol,color in [
        ('pintura','pintura_acento',d['pintura']),('oscuro','hierro','#29282c'),
        ('gris','metal','#97948c'),('llanta','metal','#4a4b4c' if d['id']=='montero_sport_blanca' else '#b0aaa0'),
        ('cromo','metal','#bfc0b9'),('neumatico','hierro','#353334'),
        ('tapizado','hierro','#49484d'),('vidrio','vidrio','#434b59'),
        ('faro','metal','#e2e6ed'),('ambar','pintura_acento','#ee9a25'),
        ('rojo','pintura_acento','#bc302d'),('matricula','metal','#d9d4cb'),
        ('azul_logo','pintura_acento','#1a365f')]:
        m[nombre]=material(rol,color)
    for nombre in ['pintura','gris','llanta','cromo','vidrio','faro']:
        bs=m[nombre].node_tree.nodes.get('Principled BSDF')
        bs.inputs['Roughness'].default_value={'pintura':.43,'gris':.46,'llanta':.34,'cromo':.26,'vidrio':.22,'faro':.23}[nombre]
        bs.inputs['Metallic'].default_value=.65 if nombre in ['llanta','cromo'] else .08
    bs=m['vidrio'].node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.32
    bs.inputs['Specular IOR Level'].default_value=.22
    bs.inputs['Alpha'].default_value=.58
    m['vidrio'].diffuse_color=(*m['vidrio'].diffuse_color[:3],.58)
    m['vidrio'].surface_render_method='DITHERED'
    m['vidrio'].use_transparent_shadow=True
    goma=m['neumatico']
    bs=goma.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=.85
    tex=goma.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(VEHICULOS/'texturas/Rubber004_1K-JPG_NormalGL.jpg'),check_existing=True)
    tex.image.colorspace_settings.name='Non-Color'
    tex.image.pack()
    normal=goma.node_tree.nodes.new('ShaderNodeNormalMap')
    normal.inputs['Strength'].default_value=.20
    goma.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color'])
    goma.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
    return m


def validar(t):
    obs=[o for o in bpy.context.scene.objects if o.type=='MESH']
    puntos=[o.matrix_world@Vector(c) for o in obs for c in o.bound_box]
    minimo=[min(p[i] for p in puntos) for i in range(3)]
    maximo=[max(p[i] for p in puntos) for i in range(3)]
    tris=malos=0
    for o in obs:
        o.data.calc_loop_triangles()
        tris+=len(o.data.loop_triangles)
        malos+=sum(tri.area<1e-11 for tri in o.data.loop_triangles)
        assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
    assert malos==0,malos
    assert abs(minimo[2])<.01,('Contacto',minimo)
    assert 15000<tris<t.d['presupuesto_triangulos'],('Presupuesto',tris)
    reporte={'id':t.id,'nombre':t.d['nombre'],'triangulos':tris,'mallas':len(obs),
             'materiales':len({m.name for o in obs for m in o.data.materials}),
             'triangulos_degenerados':malos,'limite_min_blender_m':minimo,'limite_max_blender_m':maximo,
             'dimensiones_blender_m':[maximo[i]-minimo[i] for i in range(3)],
             'escala':'Estimada desde fotos y lámina; no es un plano acotado.',
             'referencia':t.d['referencia'],'movimiento':t.g['raiz']['movimiento'].to_dict(),
             'normal_goma':{'fuente':'https://ambientcg.com/view?id=Rubber004','licencia':'CC0 1.0','empaquetado':True},
             'limites':['Vistas ocultas e interior interpretados.','Puertas cerradas, sin animación de apertura.',
                        'Cinemática plana; rutas, pendientes y colisiones urbanas pendientes.'],
             'calidad_urbana':'No aplica calidad.py de manzanas: vehículo local sin emplazamiento.'}
    (SALIDA/(t.id+'.ficha.json')).write_text(json.dumps(reporte,ensure_ascii=False,indent=2)+'\n')
    print('FLOTA_VALIDACION',json.dumps(reporte,ensure_ascii=False),flush=True)


def estudio(t,renderizar=True):
    escena=bpy.context.scene
    escena.render.engine='CYCLES'
    escena.cycles.samples=24
    escena.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='CUDA'
    prefs.get_devices()
    for dev in prefs.devices:
        dev.use=dev.type=='CUDA'
    escena.cycles.device='GPU'
    escena.world=bpy.data.worlds.new('Estudio cálido lavanda')
    escena.world.use_nodes=True
    bg=escena.world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value=(.48,.46,.52,1)
    bg.inputs['Strength'].default_value=.45
    escena.view_settings.view_transform='AgX'
    bpy.ops.mesh.primitive_plane_add(size=180,location=(0,0,-.012))
    bpy.context.object.name='ESTUDIO_suelo'
    bpy.context.object.data.materials.append(material('calzada','#b7adb5'))
    for nombre,pos,energia,size,color in [
        ('Principal',(4,-5,7),1200,5,(1,.88,.78)),('Relleno',(-4,-1,5),650,5,(.79,.85,1)),
        ('Recorte',(0,5,6),1100,4,(1,.94,.86))]:
        data=bpy.data.lights.new(nombre,'AREA')
        data.energy,data.shape,data.size,data.color=energia,'DISK',size,color
        o=bpy.data.objects.new(nombre,data)
        escena.collection.objects.link(o)
        o.location=pos
        o.rotation_euler=(Vector((0,0,.9))-o.location).to_track_quat('-Z','Y').to_euler()
    d=t.d
    h=d['alto']/2
    vistas=[('perspectiva',(8,-11,4.6),(0,0,h),d['largo']+1.25,1100,760),
            ('lateral',(0,-12,h),(0,0,h),d['largo']+.8,1200,570),
            ('frente',(12,0,h),(0,0,h),d['ancho']+1,800,700),
            ('trasera',(-12,0,h),(0,0,h),d['ancho']+1,800,700),
            ('peaton',(7,-10,1.6),(0,0,h),d['largo']+1.1,1100,740),
            ('rueda',(d['ejes'][1]+.60,-2.8,.85),(d['ejes'][1],-d['semivia_ruedas'],d['radio_rueda']),1.25,900,800)]
    cams={}
    for nombre,pos,obj,escala,rx,ry in vistas:
        data=bpy.data.cameras.new(nombre)
        o=bpy.data.objects.new(nombre,data)
        escena.collection.objects.link(o)
        o.location=pos
        o.rotation_euler=(Vector(obj)-o.location).to_track_quat('-Z','Y').to_euler()
        data.type,data.ortho_scale='ORTHO',escala
        cams[nombre]=o
    escena.camera=cams['perspectiva']
    escena.render.resolution_x,escena.render.resolution_y=1100,760
    escena.render.resolution_percentage=100
    escena.render.image_settings.file_format='PNG'
    ref=RAIZ/'autos/generadas'/(d['referencia']+'_diseno_miciudad.png')
    im=bpy.data.images.load(str(ref),check_existing=True)
    im.pack()
    im.use_fake_user=True
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=t.g['raiz']
    for pantalla in bpy.data.screens:
        for area in pantalla.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.shading.color_type='MATERIAL'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(SALIDA/(t.id+'.blend')))
    carpeta=REVISION/t.id
    carpeta.mkdir(parents=True,exist_ok=True)
    seleccion=next((a.split('=',1)[1].split(',') for a in sys.argv if a.startswith('--vistas=')),None)
    if renderizar:
        for nombre,pos,obj,escala,rx,ry in vistas:
            if seleccion and nombre not in seleccion:
                continue
            escena.camera=cams[nombre]
            escena.render.resolution_x,escena.render.resolution_y=rx,ry
            escena.render.filepath=str(carpeta/(nombre+'.png'))
            bpy.ops.render.render(write_still=True)


def main():
    catalogo=json.loads((AQUI/'disenos.json').read_text())
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if not args or args[0] not in catalogo:
        raise SystemExit('Elegir un vehículo: '+', '.join(catalogo))
    identificador=args[0]
    if 'datos' in catalogo[identificador]:
        from importlib import import_module
        constructor = import_module(f'{identificador}.construir_{identificador}')
        constructor.main([*args[1:], '--publicar'])
        return
    d=dict(catalogo[identificador],id=identificador)
    configuracion=json.loads((AQUI/'configuracion.json').read_text())
    d['movimiento']=dict(configuracion['movimiento'],**d.get('movimiento',{}))
    d['presupuesto_triangulos']=configuracion['presupuesto_triangulos']
    SALIDA.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system='METRIC'
    t=Taller(identificador,d,materiales(d))
    cuerpo(t)
    cabina(t)
    interior(t)
    frente(t)
    trasera(t)
    accesorios(t)
    ruedas(t)
    t.consolidar()
    preparar_movimiento(d,t.g)
    bpy.context.view_layer.update()
    validar(t)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(SALIDA/(identificador+'.glb')),export_format='GLB',
                              use_selection=True,export_yup=True,export_extras=True,export_animations=True,
                              export_animation_mode='NLA_TRACKS',export_force_sampling=True,export_frame_range=False,
                              export_cameras=False,export_lights=False,export_texcoords=True,export_tangents=True)
    estudio(t,'--sin-render' not in args)


if __name__=='__main__':
    main()
