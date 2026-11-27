# Integración · Mitsubishi Montero Sport Blanca (`mitsubishi_montero_sport_blanca`)

Contrato completo para cargar, conducir, recolorear e integrar la SUV en Three.js / Mi Ciudad.

## 1. Archivos publicados

```text
web/public/models/ciudad/antigravity/vehiculos/mitsubishi_montero_sport_blanca/
```

Visor interactivo local:

<http://localhost:3000/models/ciudad/antigravity/vehiculos/mitsubishi_montero_sport_blanca/index.html>

| Variante | GLB listo para cargar | Blender editable (`.blend`) | Pintura sRGB |
|---|---|---|---|
| **Blanca perlada** *(maestro)* | `mitsubishi_montero_sport_blanca.glb` / `_blanca.glb` | `mitsubishi_montero_sport_blanca.blend` / `_blanca.blend` | `#f3efe9` |
| **Plata metálico** | `mitsubishi_montero_sport_blanca_plata.glb` | `mitsubishi_montero_sport_blanca_plata.blend` | `#aeb5c0` |
| **Gris grafito** | `mitsubishi_montero_sport_blanca_grafito.glb` | `mitsubishi_montero_sport_blanca_grafito.blend` | `#4c525e` |
| **Rojo burdeos** | `mitsubishi_montero_sport_blanca_guinda.glb` | `mitsubishi_montero_sport_blanca_guinda.blend` | `#7d242d` |

## 2. Escala, ejes y jerarquía

| Propiedad | Valor |
|---|---|
| Dimensiones aproximadas | `4,76 m` largo × `1,85 m` ancho carrocería × `1,88 m` alto con barras |
| Radio de rodadura (`radio_rueda`) | `0,425 m` |
| Ejes `[eje_trasero, eje_delantero]` | `[-1,26 m, +1,48 m]` (batalla `2,74 m`) |
| Semivía (`semivia`) | `0,785 m` (vía `1,57 m`) |
| Origen y ejes GLB | Suelo en `Y = 0`, centro longitudinal; `+X` frente, `+Y` arriba, `+Z` derecha |
| Clips NLA | `rodar_adelante` y `rodar_atras` (25 muestras, 1 vuelta exacta en 1,0 s) |

## 3. Carga en Three.js

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VehiculoAnimado } from './cinematica_vehiculo.mjs';
import { aplicarVariante } from './colores_vehiculo.mjs';

const BASE = '/models/ciudad/antigravity/vehiculos/mitsubishi_montero_sport_blanca';
const gltf = await new GLTFLoader().loadAsync(`${BASE}/mitsubishi_montero_sport_blanca.glb`);
const catalogo = await fetch(`${BASE}/mitsubishi_montero_sport_blanca.variantes.json`).then(r => r.json());
const paletas = Object.fromEntries(catalogo.variantes.map(v => [v.id, v]));

const suv = gltf.scene.clone(true);
aplicarVariante(suv, 'blanca', paletas, { nombreRaiz: 'mitsubishi_montero_sport_blanca' });
escena.add(suv);

const controlador = new VehiculoAnimado(suv, null, 'mitsubishi_montero_sport_blanca');
controlador.teletransportar({ x: 0, y: alturaCalzada, z: 0, rumbo: 0 }, true);
controlador.entrada({ velocidad: 30 / 3.6, direccion: 0 });
// Por cada fotograma:
controlador.actualizar(dt);
```
