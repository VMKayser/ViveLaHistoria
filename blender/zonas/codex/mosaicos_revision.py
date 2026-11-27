"""Mosaicos del recorrido a pie y comprobación de cobertura de cada cámara.
No fuerza archivos ignorados a Git; todo queda en revisiones/codex/.
"""
import json,hashlib,sys
from pathlib import Path
from PIL import Image,ImageDraw
raiz=Path(__file__).resolve().parents[3]
base=raiz/'revisiones/codex/recorrido'
datos=json.loads((base/'camaras.json').read_text())
claves=[(c['manzana'],c['nombre']) for c in datos['camaras']]
assert len(claves)==len(set(claves)), 'Hay cámaras duplicadas en el recorrido'
inicio=(base/'camaras.json').stat().st_mtime
if '--parcial' not in sys.argv:
    assert {c['manzana'] for c in datos['camaras']}==set(datos['modelos_sha256']), 'El recorrido no cubre todas las manzanas'
for mid,h in datos['modelos_sha256'].items():
    actual=hashlib.sha256((raiz/'web/public/models/ciudad/codex'/f'{mid}.glb').read_bytes()).hexdigest()
    assert h==actual,('El modelo cambió después de renderizar',mid)
imgs=[]
for c in datos['camaras']:
    assert c.get('modelo_sha256',datos['modelos_sha256'][c['manzana']])==datos['modelos_sha256'][c['manzana']],('Falta repetir las vistas del modelo cambiado',c['manzana'])
    inicio_camara=c.get('inicio_revision_unix',inicio)
    p=base/c['manzana']/(c['nombre']+'.jpg')
    if '--parcial' in sys.argv and (not p.exists() or p.stat().st_mtime<inicio_camara):break
    assert p.exists(),('Falta vista',p)
    assert p.stat().st_mtime>=inicio_camara,('La vista pertenece a un recorrido anterior',p)
    with Image.open(p) as im:im.verify()
    imgs.append((c['manzana']+' '+c['nombre'],p))
out_dir=raiz/'revisiones/codex/calidad_E';out_dir.mkdir(exist_ok=True)
for pagina,inicio in enumerate(range(0,len(imgs),12),1):
    lote=imgs[inicio:inicio+12];out=Image.new('RGB',(1600,325*((len(lote)+3)//4)),'#eee8df');d=ImageDraw.Draw(out)
    for i,(nombre,p) in enumerate(lote):
        im=Image.open(p);im.thumbnail((400,300));x=(i%4)*400;y=(i//4)*325
        d.text((x+5,y+5),nombre,fill='black');out.paste(im,(x,y+24))
    out.save(out_dir/f'mosaico_{pagina:02}.jpg')
print(f'{len(imgs)}/{len(datos["camaras"])} vistas en {(len(imgs)+11)//12} mosaicos; hashes de los modelos coinciden.')
