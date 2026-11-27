# Integración del autobús BRONCO

Guía para el desarrollador o agente que recibe el vehículo. No requiere conocer la conversación de modelado.
Describe los archivos entregados, cómo cargar y conducir el autobús, cambiar color y velocidad y conectarlo al proyecto.

## 1. Qué se entrega

Los archivos publicados están en:

```text
web/public/models/ciudad/codex/vehiculos/
```

En la web se sirven desde `/models/ciudad/codex/vehiculos/` (la URL no incluye `web/public`).

| Color | GLB listo para cargar | Blender editable |
|---|---|---|
| Azul | `autobus_bronco_azul.glb` | `autobus_bronco_azul.blend` |
| Rojo | `autobus_bronco_rojo.glb` | `autobus_bronco_rojo.blend` |
| Amarillo | `autobus_bronco_amarillo.glb` | `autobus_bronco_amarillo.blend` |
| Verde | `autobus_bronco_verde.glb` | `autobus_bronco_verde.blend` |

`autobus_bronco.glb` y `autobus_bronco.blend` siguen siendo el maestro azul compatible con los enlaces anteriores.
Los archivos con sufijo `_azul` son copias idénticas. `autobus_bronco.variantes.json` enumera archivos, colores,
tamaños y hashes. Los cuatro GLB comparten exactamente el mismo bloque binario: geometría, UV, normales,
textura y muestras de animación. Solo cambia la pintura y la identificación de variante.

Otros archivos:

| Archivo | Uso |
|---|---|
| `autobus_animado.mjs` | Adaptador de la jerarquía a Three.js |
| `cinematica_vehiculo.mjs` | Movimiento, aceleración, frenada, Ackermann y rodadura por distancia |
| `colores_bronco.mjs` | Cambio de pintura por instancia sin alterar otras instancias |
| `autobus_bronco.ficha.json` | Medidas, conteos y datos técnicos del modelo común |
| `index.html`, `visor.bundle.js` | Visor de revisión y conducción, no el sistema de tráfico de la ciudad |
| `THREE-LICENSE.txt` | Licencia del software usado por el visor |
| `GUIA_PARA_CREAR_SKILL_VEHICULOS.md` | Proceso de producción y encargo para crear una skill |

Las fuentes están en `blender/zonas/codex/vehiculos/`.
El normal de goma Rubber004 de ambientCG es CC0; está empaquetado en los modelos.
Su procedencia se registra en `texturas/LICENCIA.txt` y `recursos/LICENCIAS.md` del repositorio.
No hace falta descargar una textura para usar los GLB.

## 2. Probar el vehículo

Con el servidor del proyecto abierto:

<http://localhost:3000/models/ciudad/codex/vehiculos/index.html>

Si no hay servidor, el comando habitual es `cd web && npm run dev`. Usar HTTP; abrir el HTML como `file://`
puede bloquear la carga de modelos y módulos.

- Elegir Azul, Rojo, Amarillo o Verde. Los enlaces de descarga corresponden al color seleccionado.
- **Probar marcha** inicia una prueba circular con aceleración y dirección suaves; **Frenar** detiene el vehículo.
- Mantener flechas o W/A/S/D para conducir; espacio frena. Los mandos táctiles admiten aceleración y giro simultáneos.
- **Reiniciar** vuelve al origen y reinicia las ruedas sin vueltas ficticias.
- Las vistas, **Rueda**, **Girar vista** y **Malla** sirven para inspección. La cámara acompaña al vehículo.

La prueba circular y su cuadrícula pertenecen al visor de revisión. No son una ruta real ni una calle de la ciudad.

## 3. Escala, origen y coordenadas

| Propiedad | Valor |
|---|---|
| Unidades | Metros; segundos y radianes en el controlador |
| Carrocería aproximada | 6,4 m de largo × 2,14 m de ancho × 3,15 m de alto |
| Radio de rodadura | 0,49 m |
| Eje trasero, X local | −1,63 m |
| Eje delantero, X local | +1,92 m |
| Distancia entre ejes | 3,55 m |
| Semivía de ruedas | 0,965 m; vía de 1,93 m |
| Origen | Centro longitudinal del vehículo, a nivel del suelo |
| Blender | +X frente, +Y izquierda, +Z arriba |
| GLB / Three.js | +X frente, +Y arriba, +Z derecha |

Las medidas son estimadas desde el diseño, no de un plano acotado. El ancho con espejos y el largo con parachoques
superan las medidas de carrocería; consultar los límites de la ficha para volúmenes de colisión.

Con `rumbo = 0` el autobús mira hacia +X. Un rumbo positivo alrededor de Y gira hacia −Z (izquierda).
El controlador trabaja en las coordenadas del padre de `autobus_bronco`; ese padre debe tener escala unitaria.
No interpretar estas coordenadas locales como una ubicación ya elegida dentro de Sucre.

## 4. Jerarquía que hay que conservar

```text
autobus_bronco
├── carroceria / interior / cristales / decoracion
├── direccion_delantera_derecha
│   └── rueda_delantera_derecha
├── direccion_delantera_izquierda
│   └── rueda_delantera_izquierda
├── rueda_trasera_derecha
├── rueda_trasera_izquierda
└── puerta_pivote
```

Las mallas están agrupadas por material debajo de esos nodos; sus nombres no constituyen un selector de color.
Los nombres de raíz, dirección y ruedas sí forman el contrato del controlador.
No fusionar las ruedas en la carrocería ni en los lotes estáticos de edificios.

El nodo raíz lleva `userData.movimiento` al cargarlo con GLTFLoader. Incluye geometría de ejes y límites de marcha.
Los nombres y el rig son iguales en los cuatro colores. La puerta conserva la posición abierta del diseño;
no se incluye un sistema automático de apertura/cierre.

## 5. Cargarlo en Three.js

El proyecto usa Next.js y Three.js. Añadir la carga al lado cliente del visor existente.
Los módulos entregados no importan otra copia de Three: operan sobre los objetos que crea el GLTFLoader de la aplicación.
Se pueden trasladar los tres `.mjs` a una carpeta de código del proyecto manteniendo sus imports relativos,
o usarlos directamente en un visor con módulos ES desde la carpeta pública.

Ejemplo para un código cliente con una `escena` Three ya creada:

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { AutobusAnimado } from './autobus_animado.mjs';

const BASE = '/models/ciudad/codex/vehiculos';
const loader = new GLTFLoader();

async function crearAutobus(escena, color, pose, limites = {}) {
  if (!['azul', 'rojo', 'amarillo', 'verde'].includes(color)) {
    throw new Error('Color de autobús desconocido');
  }
  const gltf = await loader.loadAsync(`${BASE}/autobus_bronco_${color}.glb`);
  const raiz = gltf.scene.getObjectByName('autobus_bronco');
  const configuracion = { ...raiz.userData.movimiento, ...limites };
  const controlador = new AutobusAnimado(gltf.scene, configuracion);
  controlador.teletransportar(pose, true);
  escena.add(gltf.scene);
  return { modelo: gltf.scene, controlador, clips: gltf.animations };
}

const autobus = await crearAutobus(escena, 'rojo', {
  x: 20, y: alturaCalzada, z: -10, rumbo: 0,
});
autobus.controlador.entrada({ velocidad: 3, direccion: 0 });
```

`alturaCalzada` debe venir del sistema de calles. Los números del ejemplo son una colocación ficticia.
No cargar todos los colores para mostrar un solo autobús: elegir un archivo o cargar una vez y recolorear instancias.

En el bucle de render **ya existente**, antes de dibujar:

```js
// dt en segundos; calcularlo una sola vez por fotograma en la aplicación.
autobus.controlador.actualizar(dt);
```

No crear un segundo bucle independiente para las ruedas. En la demo se limita un salto de tiempo de dibujo a 0,1 s
y se reinicia la referencia temporal al cambiar la visibilidad de la pestaña, para no recuperar de golpe tiempo en segundo plano.

## 6. API de conducción

| Método | Efecto |
|---|---|
| `entrada({ velocidad, direccion })` | Fija objetivos; acelera, frena y mueve el volante gradualmente al actualizar |
| `actualizar(dt)` | Integra movimiento y actualiza raíz, dirección y rodadura; devuelve el estado |
| `avanzarDistancia(ds, k = 0)` | Integra directamente el arco firmado del eje trasero y su curvatura |
| `teletransportar({ x, z, rumbo, y? }, reiniciarRuedas = false)` | Coloca sin rodar las ruedas; detiene velocidad y dirección |
| `estado()` | Devuelve pose, velocidad, dirección y, por rueda, distancia, rodadura y dirección |

Una entrada se mantiene hasta cambiarla. No hace falta repetirla si el objetivo no ha cambiado.
Velocidad positiva avanza; negativa retrocede. Dirección positiva gira a la izquierda; negativa a la derecha.
`direccion` es el ángulo de la rueda virtual central del modelo cinemático; los dos ángulos delanteros reales
los calcula Ackermann. No asignarles el mismo ángulo manualmente.

```js
const bus = autobus.controlador;
bus.entrada({ velocidad: 18 / 3.6, direccion: 0 });       // 18 km/h
bus.entrada({ velocidad: 8 / 3.6, direccion: 0.20 });     // curva a la izquierda
bus.entrada({ velocidad: 0, direccion: 0 });             // frenar suavemente
bus.entrada({ velocidad: -5 / 3.6, direccion: -0.12 });   // marcha atrás y volante a la derecha
```

El cambio de sentido frena hasta cero antes de acelerar al revés. Al parar no siguen girando las ruedas.
El modelo utiliza distancia por rueda / radio y pasos de integración de hasta 1/120 s.

## 7. Cambiar velocidad y comportamiento

**Cambiar el objetivo no es cambiar el límite.** Una entrada de 40 km/h se limita al máximo configurado si ese máximo es 30.
Para cambiar límites por vehículo, pasar una copia de la configuración al constructor:

```js
const base = gltf.scene.getObjectByName('autobus_bronco').userData.movimiento;
const bus = new AutobusAnimado(gltf.scene, {
  ...base,
  velocidad_maxima: 40 / 3.6,
  retroceso_maximo: 6 / 3.6,
  aceleracion: 1.1,
  frenada: 2.4,
});
bus.entrada({ velocidad: 25 / 3.6, direccion: 0 });
```

Esto no requiere regenerar ni recolorear el modelo. La configuración se copia al construir cada controlador;
no mutar internamente `cinematica.config` para cambiar su geometría durante la marcha.

| Campo | Unidad | Valor publicado |
|---|---|---|
| `velocidad_maxima` | m/s | 8,333… = 30 km/h |
| `retroceso_maximo` | m/s, magnitud positiva | 2 = 7,2 km/h |
| `aceleracion` | m/s² | 1,25 |
| `frenada` | m/s² | 2,6 |
| `direccion_maxima` | radianes | 0,48 ≈ 27,5° |
| `rapidez_direccion` | radianes/s | 0,65 |
| `radio_rueda` | m | 0,49; debe corresponder a la geometría |
| `eje_trasero`, `eje_delantero` | m, X local | −1,63; +1,92 |
| `semivia` | m | 0,965 |

Para cambiar los valores publicados por defecto, editar `movimiento` en `bronco.json` y regenerar el maestro y variantes.
Radio de rueda, ejes y semivía son medidas del modelo: no usarlas como controles de velocidad.

Los parámetros de la prueba independiente son distintos:

- `movimiento.velocidad_demo = 2.5` m/s (9 km/h) y `radio_demo = 12` m, en `bronco.json`.
- En el visor, los botones manuales piden 4 m/s hacia delante y 1,5 m/s en reversa, en `actualizarMarcha` de `visor.js`.
- Cambiar solo la demo o sus botones requiere volver a ejecutar `preparar_visor.cjs`; no editar el bundle minificado.
- El radio mínimo que permite la dirección es aproximadamente `batalla / tan(direccion_maxima)`; con estos datos, 6,82 m.

## 8. Conectarlo a rutas, alturas y colisiones

El controlador ya mueve el vehículo. El planificador de rutas debe proporcionarle objetivos de velocidad/dirección,
o distancia/curvatura. No mover además `modelo.position` a mano: la pose y las vueltas dejarían de concordar.

Alternativa para una ruta parametrizada por longitud:

```js
// ds: metros firmados de arco del centro del eje trasero durante este paso.
// k: curvatura firmada en 1/m; 0 = recta, 1/12 = curva izquierda de radio 12 m.
bus.avanzarDistancia(ds, k);
```

En ese modo no llamar también `actualizar(dt)` para el mismo avance. `avanzarDistancia` no recibe tiempo:
la velocidad de su interfaz se calcula fuera, con `ds / dt`; no asumir que `estado().velocidad` se actualiza en ese modo.
El arco corresponde al eje trasero, no a la cuerda entre dos posiciones del centro visual del autobús.

Para colocar un vehículo al aparecer, cambiar de tramo o recargar una partida, usar `teletransportar`.
El segundo argumento `true` también reinicia la fase de ruedas; con `false`, conserva la fase sin añadir vueltas por el salto.

**Lo que queda a cargo de la aplicación:** rutas reales, seguimiento de carril, otros vehículos, semáforos, paradas,
altura/orientación sobre la calzada, pendientes, contactos de neumáticos y colisiones.
Este controlador es cinemático sobre un plano. Cambiar solo Y no resuelve por sí mismo la rodadura y orientación
en una pendiente; el adaptador del terreno debe aportar alturas/contactos y distancia coherente con esa superficie.
No se entrega una simulación de suspensión ni físicas de impactos.

En Mi Ciudad, no registrarlo en los manifiestos de manzanas ni mezclarlo en los lotes estáticos de fachadas.
Debe cargarse como un actor móvil conservando su jerarquía y materiales, incluido el normal del neumático.
Respetar las responsabilidades de archivos establecidas en `AGENTS.md` al conectar el visor urbano.

## 9. Colores e instancias

Paleta sRGB de la pintura:

| Variante | Principal | Detalle |
|---|---|---|
| Azul | `#0343b8` | `#1553c0` |
| Rojo | `#bd292e` | `#d74142` |
| Amarillo | `#e3b51b` | `#f0c93d` |
| Verde | `#1b7b4b` | `#32945e` |

Cargar un GLB de color no requiere recoloración adicional. Para cambiar de color sin descargar de nuevo el vehículo,
o para clonar el maestro varias veces:

```js
import { aplicarVariante } from './colores_bronco.mjs';

const catalogo = await fetch(`${BASE}/autobus_bronco.variantes.json`).then(r => r.json());
const paletas = Object.fromEntries(catalogo.variantes.map(v => [v.id, v]));
const modelo = maestro.scene.clone(true);
aplicarVariante(modelo, 'verde', paletas);
const bus = new AutobusAnimado(modelo);
escena.add(modelo);
```

El helper clona únicamente las dos pinturas y mantiene una caché por instancia. No altera clips, rig ni estado de marcha;
cambiar a rojo mientras conduce no teletransporta ni reinicia las ruedas. No cambia luces, goma, cristal, blanco ni gráficos.
Los materiales se comparten normalmente al hacer `scene.clone(true)`; no cambiar su `.color` directamente si varias instancias
deben conservar colores distintos. Si se hacen personalizaciones fuera de las pinturas, gestionar también sus materiales.

La geometría y texturas pueden compartirse entre clones. Disponer de cuatro GLB no obliga a tener cuatro copias de geometría
en memoria. El modelo común tiene 68.848 triángulos, 45 mallas y 20 materiales; medir el coste con la población prevista.
No hay niveles de detalle automáticos incluidos.

## 10. Clips para otros motores

`rodar_adelante` y `rodar_atras` contienen una vuelta completa de las cuatro ruedas en un segundo.
Los pivotes delanteros de dirección están separados de los de rodadura. El controlador Three escribe ambos directamente.

No reproducir un `AnimationMixer` sobre los mismos pivotes mientras los controle `AutobusAnimado`.
Para una vista previa o un motor que use clips, elegir un sentido y ajustar la tasa de reproducción en recta:

```text
vueltas por segundo = abs(velocidad en m/s) / (2 × π × radio en m)
```

Con radio 0,49 m y velocidad 3 m/s, la tasa del clip es aproximadamente 0,9744.
En curvas, las cuatro tasas son diferentes; los clips uniformes no sustituyen el cálculo de arcos.
El GLB se puede importar en otros motores; los módulos `.mjs` operan sobre objetos Three y no son scripts nativos de esos motores.
Portar la cinemática o usar sus controles de vehículo conservando unidades, ejes y jerarquía.

## 11. Regeneración y validación

Desde la raíz del repositorio, con Blender disponible y dependencias instaladas en `web/`:

```sh
~/apps/blender-5.2.3-linux-x64/blender -b -t 2 \
  -P blender/zonas/codex/vehiculos/autobus_bronco.py -- --sin-render
python3 blender/zonas/codex/vehiculos/generar_variantes.py
~/apps/blender-5.2.3-linux-x64/blender \
  -b web/public/models/ciudad/codex/vehiculos/autobus_bronco.blend -t 2 \
  -P blender/zonas/codex/vehiculos/variantes_blender.py
node blender/zonas/codex/vehiculos/preparar_visor.cjs
node blender/zonas/codex/vehiculos/validar_glb.cjs
node blender/zonas/codex/vehiculos/validar_variantes.cjs
node --test blender/zonas/codex/vehiculos/movimiento.test.mjs
```

No reconstruir el vehículo por separado para cada color: el generador de variantes conserva el binario del maestro.
Para cambiar solo paletas, empezar por `generar_variantes.py`; las copias Blender usan el maestro existente.
Esto sirve para rojo, amarillo y verde. El azul se conserva desde el maestro: si se cambia su tono, actualizar también
`colores.azul` / `colores.azul_claro` y `variantes.azul` en los datos y regenerar el maestro antes de las variantes.
La fuente del visor es `visor.js`; `visor.bundle.js` se genera. Los `.md` publicados son copias de sus fuentes en `blender/zonas/codex/vehiculos/`.

La validación comprueba formato GLB, materiales/normal, rig, clips completos y colores; compara binarios y estructuras
entre variantes. Las pruebas de movimiento cubren recta, retroceso, curvas, frenada, reinicio y consistencia a 30/60/120 FPS.
El visor se prueba también en navegador y con mandos táctiles. La comprobación urbana de edificios `calidad.py` no sustituye
estas pruebas de un vehículo independiente.
