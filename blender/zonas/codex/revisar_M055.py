"""Revisión CPU del GLB exportado: alternativa a EEVEE cuando EGL no responde."""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from kit import *
from kit import salida
MID='M055'
for clave in ('M056','M037','M061','M063','M027','P01'):
    if '--'+clave.lower() in sys.argv: MID=clave
m,col=iniciar('codex',MID)
bpy.ops.import_scene.gltf(filepath=os.path.join(salida.dir_modelos('codex'),MID+'.glb'))
for ob in list(bpy.context.scene.objects):
    for cc in list(ob.users_collection): cc.objects.unlink(ob)
    col.objects.link(ob)
original=salida._luz_y_mundo
def luz_cpu():
    original()
    sc=bpy.context.scene
    sc.render.engine='CYCLES'
    sc.cycles.device='CPU'
    sc.cycles.samples=16
    sc.cycles.use_denoising='--sin-denoise' not in sys.argv
    sc.render.threads_mode='FIXED'
    sc.render.threads=int(next((a.split('=',1)[1] for a in sys.argv if a.startswith('--hilos=')),8))
salida._luz_y_mundo=luz_cpu
def camara_comparacion(archivo):
    if MID=='M063':
        from museo_codex import plano_museo
        _,l,_=plano_museo()
        f=Fachada(None,l,altura_suelo((l['a'][0]+l['b'][0])/2,(l['a'][1]+l['b'][1])/2)+.12)
        config={'130907':(f.largo+2,10,.5), '130911':(f.largo/2,10,.5),
                '130913':(f.largo*.6,10,.5), '130916':(f.largo*.25,10,.55)}
        ss,distancia,t=config[archivo[-10:-4]]
        pos=f.punto(ss,1.7,distancia);pos.z=altura_suelo(pos.x,pos.y)+1.7
        return camara(pos,f.punto(f.largo*t,4.5),lente=18)
    if MID=='P01':
        x,y,tx,ty={
            '130603':(-204,-142,-176.7,-208.9),
            '130631':(-240,-184,-190,-214),
        }[archivo[-10:-4]]
        return camara((x,y,altura_suelo(x,y)+1.7),
                      (tx,ty,altura_suelo(tx,ty)+4.3),lente=22)
    if MID in ('M061','M027'):
        eid,idx,ss,distancia,mirar_s,mirar_h,lente={
            '130923':('E02ae75',5,1,14,1,4.8,20),
            '130936':('E311863',8,35,14,35,4.8,22),
            '130941':('E311863',8,22,14,22,4.8,22),
            '130948':('E311863',8,12,14,8,4.8,22),
            '130951':('E311863',8,8,14,8,4.8,24),
            '130957':('E311863',8,6,14,8,4.8,24),
            '131000':('E311863',8,3,16,6,4.8,22),
            '131002':('E311863',8,1,14,5,5.0,22),
            '130929':('E311863',8,44,14,44,5.0,22),
            '130946':('E311863',8,18,14,18,4.8,22),
            '130954':('E311863',8,8,16,8,4.8,22),
            '130401':('Eaeb297',0,2.7,12,2.7,4.2,24),
        }[archivo[-10:-4]]
        e=edificio(MID,eid);l=lados(e['huella'])[idx]
        f=Fachada(None,l,max(altura_suelo(*p) for p in e['huella']))
        distancia=next((dd for dd in (distancia,12,10,8,6,4)
                        if not datos.dentro_de_edificio(*f.punto(ss,0,dd)[:2])),distancia)
        pos=f.punto(ss,1.7,distancia);pos.z=altura_suelo(pos.x,pos.y)+1.7
        return camara(pos,f.punto(mirar_s,mirar_h),lente=lente)
    if MID=='M037' and archivo[-10:-4] in ('130440','130357'):
        if archivo[-10:-4]=='130440':
            x,y,tx,ty=-250,-63,-273,-65
        else:x,y,tx,ty=-291,-30,-298,-52
        return camara((x,y,altura_suelo(x,y)+1.7),
                      (tx,ty,altura_suelo(tx,ty)+8),lente=20)
    if MID=='M037':
        eid,idx,ss,distancia,mirar_s,mirar_h,lente={
            '130452':('E627dd1',0,56.2,10,25,5.2,14),
            '130521':('E627dd1',0,27,10.4,27,5.0,18),
            '130638':('Ee30c62',17,42,11,15,4.5,22),
        }[archivo[-10:-4]]
        e=edificio(MID,eid)
        l=lados(e['huella'])[idx]
        f=Fachada(None,l,max(altura_suelo(*p) for p in e['huella']))
        pos=f.punto(ss,1.7,distancia)
        pos.z=altura_suelo(pos.x,pos.y)+1.6
        mirar=f.punto(mirar_s,mirar_h)
        if eid=='E627dd1':mirar.z=altura_suelo(mirar.x,mirar.y)+mirar_h
        return camara(pos,mirar,lente=lente)
    configuracion={
        '130647':('E2c6601',0,35,7.5,-8),
        '130705':('E2c6601',0,33,7.5,-4),
        '130707':('E2c6601',0,32,7.5,-2),
        '130709':('E2c6601',0,32,7.5,3),
        '130719':('E2c6601',0,32,7.5,8),
        '130724':('E03fe1d',2,27,7,-6),
        '130726':('E03fe1d',2,27,6,-3),
        '130743':('E03fe1d',0,37,9,5),
        '130838':('E03fe1d',12,13,12,6),
        '130857':('E03fe1d',12,12,8,-2),
        '130904':('E03fe1d',10,14,7,2),
        '130715':('E2c6601',0,30,7.5,0),
        '130746':('E03fe1d',0,37,8,8),
        '130751':('E03fe1d',0,37,9,4),
        '130759':('E03fe1d',0,37,10,-4),
        '130805':('E03fe1d',0,37,10.5,-8),
        '130808':('E03fe1d',0,37,11,-9),
        '130812':('E03fe1d',0,37,12,-10),
        '130755':('E03fe1d',0,37,9,0),
        '130818':('E03fe1d',0,37,12,-10),
        '130741':('E03fe1d',0,37,8,8),
        '130736':('E03fe1d',2,25,6,0),
        '130840':('E03fe1d',12,12,12,6),
        '130853':('E03fe1d',12,11,7,-3),
        '130902':('E03fe1d',10,14,6.5,0),
    }
    eid,indice,distancia,altura,desplazamiento=configuracion[archivo[-10:-4]]
    e=edificio('M055',eid)
    l=lados(e['huella'])[indice]
    z=max(altura_suelo(*p) for p in e['huella'])
    f=Fachada(None,l,z)
    if indice==10:
        from piezas_codex import trasladar
        from museo_codex import avance_museo
        f=trasladar(f,d=8.75+avance_museo())
    pos=f.punto(f.largo/2+desplazamiento,1.6,distancia)
    while datos.dentro_de_edificio(pos.x,pos.y) and distancia>4:
        distancia-=1
        pos=f.punto(f.largo/2+desplazamiento,1.6,distancia)
    if datos.dentro_de_edificio(pos.x,pos.y):
        raise ValueError('Cámara dentro de edificio: '+archivo)
    pos.z=altura_suelo(pos.x,pos.y)+1.6
    return camara(pos,
                  f.punto(f.largo/2,altura,-2),lente=14 if archivo[-10:-4] in ('130840','130853') else 24)
salida.camara_desde_foto=camara_comparacion
if '--aislado' in sys.argv:
    # Solo comprobar piezas: no sustituye la validación de implantación.
    salida.contexto=lambda mid: None
fotos=('130755','130818') if MID=='M056' else ('130715','130736','130741','130840','130853')
if MID=='P01': fotos=('130603','130631')
if MID=='M061': fotos=('130929','130946','130954')
if MID=='M055' and '--todas' in sys.argv: fotos=tuple(n[-10:-4] for n in m['fotos'] if n[-10:-4] not in ('130907','130911','130913','130916'))
if MID=='M061' and '--todas' in sys.argv: fotos=tuple(n[-10:-4] for n in m['fotos'])
if MID=='M056' and '--todas' in sys.argv: fotos=tuple(n[-10:-4] for n in m['fotos'])
if MID=='M027': fotos=('130401',)
if MID=='M063': fotos=('130907','130911','130913','130916')
if MID=='M037': fotos=('130452','130521','130638')
if '--san-miguel' in sys.argv: fotos=('130440','130357')
if '--conjunto' in sys.argv: fotos=('130452','130521','130638','130440','130357')
if '--torre' in sys.argv: fotos=('130853','130840')
if '--palacio' in sys.argv: fotos=('130715',)
if '--catedral' in sys.argv: fotos=('130736','130741','130853','130840','130902')
if '--fotos' in sys.argv:
    fotos=tuple(sys.argv[sys.argv.index('--fotos')+1].split(','))
extras=[]
if '--cuadra-aerea' in sys.argv:
    extras=[('cuadra_aerea',(-165,-195,altura_suelo(-265,-280)+110),
              (-268,-280,altura_suelo(-268,-280)+5))]
if MID=='P01': extras=[('aerea',(-290,-330,180),(-176.7,-208.9,64))]
# Elegir la región desde las cámaras concretas antes de importar contexto.
from contexto_codex import instalar_contexto
puntos=[]
for n in fotos:
    ob=camara_comparacion('IMG_20261105_'+n+'.jpg');puntos.append(tuple(ob.location))
    puntos.append(tuple(ob.location+ob.rotation_euler.to_quaternion()@__import__('mathutils').Vector((0,0,-30))))
for _,p,q in extras:puntos.extend([p,q])
base=None
if '--base-borrador' in sys.argv:
    base=os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113/BASE_limpia.glb')
    salida.dir_revision=lambda ag,mid:os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113',mid+'_base_borrador')
instalar_contexto(puntos,margen=24,base_alternativa=base)
if '--sin-relleno' in sys.argv:
    original_contexto=salida.contexto
    def diagnostico(mid):
        original_contexto(mid)
        for ob in bpy.data.objects:
            if ob.name.startswith('BASE_relleno'):ob.hide_render=True
    salida.contexto=diagnostico
    salida.dir_revision=lambda ag,mid:os.path.join(datos.RAIZ,'revisiones/codex/repaso_20261113',mid+'_sin_relleno')
revisar('codex',MID,camaras_extra=extras,fotos=['IMG_20261105_'+n+'.jpg' for n in fotos],ancho=900,alto=675)
