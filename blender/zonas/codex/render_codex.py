"""Configuración común de revisión local en la NVIDIA, sin denoiser pesado."""
import bpy


def configurar(sc,hilos=2,muestras=8):
    preferencias=bpy.context.preferences.addons['cycles'].preferences
    preferencias.compute_device_type='CUDA';preferencias.get_devices()
    encontrados=[]
    for dispositivo in preferencias.devices:
        dispositivo.use=dispositivo.type=='CUDA'
        if dispositivo.use:encontrados.append(dispositivo.name)
    assert encontrados,'No se encontró la NVIDIA para revisar a pie'
    sc.render.engine='CYCLES';sc.cycles.device='GPU'
    sc.cycles.samples=muestras;sc.cycles.use_denoising=False
    sc.render.threads_mode='FIXED';sc.render.threads=hilos
    print('[render codex] NVIDIA CUDA:',', '.join(encontrados),flush=True)
