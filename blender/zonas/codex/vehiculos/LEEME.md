# Autobús BRONCO

Cuatro colores disponibles: **azul, rojo, amarillo y verde**, con GLB y Blender por color.
Elegir el color en el visor; sus botones de descarga corresponden a la variante seleccionada.
`autobus_bronco.variantes.json` es el catálogo. El maestro sin sufijo sigue siendo azul.

Documentación de entrega:

- [Proceso y encargo para crear una skill](GUIA_PARA_CREAR_SKILL_VEHICULOS.md).
- [Integración, API, velocidades, colores y regeneración](INTEGRACION_VEHICULOS.md).

Modelo realizado a mano mediante geometría de Blender desde la lámina blanca/azul adjunta por el usuario el 24/11/2026.
La referencia original se conserva en `referencia.png`. Las formas, vanos, franjas y gráficos se definen explícitamente en `autobus_bronco.py`; dimensiones y colores en `bronco.json`.
La carrocería y las ruedas están modeladas en el proyecto. El microrelieve de goma utiliza el normal OpenGL de Rubber 004 (ambientCG, CC0), empaquetado en GLB y Blender; no cambia el color base. Fuente y licencia en `texturas/LICENCIA.txt` y `recursos/LICENCIAS.md`.

## Revisar

Con el servidor habitual `cd web && npm run dev`:

<http://localhost:3000/models/ciudad/codex/vehiculos/index.html>

El visor permite mirar el modelo y **Probar marcha**, frenar y reiniciar. Las flechas de pantalla o W/A/S/D permiten
conducir, incluso en retroceso; espacio frena. La cámara sigue al autobús. Sirve el GLB real.
Funciona con las dependencias existentes del proyecto; no necesita CDN ni conexión externa.

También se puede abrir `web/public/models/ciudad/codex/vehiculos/autobus_bronco.blend`. Contiene el modelo,
el estudio, cámaras nombradas y la referencia empaquetada. El GLB exporta únicamente el vehículo.

## Regenerar

```sh
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  ~/apps/blender-5.2.3-linux-x64/blender -b -t 2 \
  -P blender/zonas/codex/vehiculos/autobus_bronco.py -- --sin-render
python3 blender/zonas/codex/vehiculos/generar_variantes.py
~/apps/blender-5.2.3-linux-x64/blender \
  -b web/public/models/ciudad/codex/vehiculos/autobus_bronco.blend -t 2 \
  -P blender/zonas/codex/vehiculos/variantes_blender.py
node blender/zonas/codex/vehiculos/preparar_visor.cjs
node blender/zonas/codex/vehiculos/validar_glb.cjs
node blender/zonas/codex/vehiculos/validar_variantes.cjs
node --test blender/zonas/codex/vehiculos/movimiento.test.mjs blender/zonas/codex/vehiculos/colores.test.mjs
```

Omitir `--sin-render` para generar las vistas en `revisiones/codex/autobus_bronco/`.
Ejecutar un único render pesado a la vez. El estudio usa NVIDIA CUDA cuando está disponible. Para repetir solo una vista, usar `-- --vistas=trasera` (admite nombres separados por comas).

## Convención de integración

- Metros reales estimados: carrocería de 6,4 × 2,14 × 3,15 m; el ancho total incluye los espejos.
- Origen sobre el suelo, centro longitudinal. En Blender el frente apunta a +X, Z arriba; GLB convierte a Y arriba.
- Cuatro pivotes de rodadura. Los dos delanteros tienen un padre `direccion_delantera_derecha/izquierda` que gira
  alrededor de Z en Blender / Y en GLB. Rodadura alrededor de +Y local en Blender / −Z local en GLB al avanzar.
- Dos clips GLB y Blender: `rodar_adelante` y `rodar_atras`. Cada uno da una vuelta por segundo en las cuatro ruedas.
- Puerta abierta con pivote independiente; las dos hojas están en posición plegada.
- Carrocería, interior, acristalamiento y decoraciones agrupados por material. Materiales con roles existentes de la paleta.
- No se registra como manzana: no se agrega al manifiesto urbano ni se coloca en el origen de la ciudad.
- Controlador reutilizable entregado; la colocación, rutas y carga en el visor urbano corresponden a su mantenedor según AGENTS.md.

## Fidelidad y límites

La lámina es la referencia del frente, del lateral de acceso, de la trasera y del aspecto general. Se reconstruyen
techo de hombros elípticos, morro curvo, ventanillas con esquinas redondeadas, puerta abierta y tres peldaños,
neumáticos abombados con canales y cortes de rodadura, llantas de acero cóncavas con seis ventilaciones realmente abiertas,
faros dobles, pilotos de tres colores, espejos, limpiaparabrisas, emblemas y letras BRONCO.
El caballo y las filigranas son geometría vectorial reconstruida, no calcos exactos a píxel.

Sin medidas acotadas ni vista del otro lateral o del interior, esos elementos se interpretan. Las vistas de la
lámina también difieren ligeramente en perspectiva y detalles; la vista lateral determina la longitud y los vanos.
No se afirma una coincidencia exacta ni aprobación visual del usuario.

El informe `autobus_bronco.ficha.json` registra límites y conteos. El control urbano `calidad.py` analiza manzanas
emplazadas, postes y edificios; no valida un vehículo independiente. El GLB se comprueba además con gltf-validator.

## Corrección de curvaturas y ruedas

`acabados_bronco.py` contiene las superficies de techo, el perfil frontal con tangencias suaves y el redondeo en planta.
La misma transformación se aplica a chapas, marcos, cristales y piezas del frente para conservar su ajuste.
Las ruedas se construyen por revolución y operaciones de corte, con UV propios para el normal de goma.
El dibujo principal de rodadura es geometría; el normal añade solamente grano fino.

## Movimiento e integración

`cinematica_vehiculo.mjs` integra avance/retroceso, aceleración, frenada y dirección Ackermann.
Calcula los cuatro arcos de rueda por separado y divide cada distancia firmada por el radio de 0,49 m.
Así la rodadura depende del desplazamiento, y cada rueda recorre su propio arco en las curvas. Los pasos de integración
son de hasta 1/120 s; no dependen de los FPS de dibujo. La prueba circular pertenece exclusivamente a este visor de revisión.

`autobus_animado.mjs` adapta ese cálculo a la jerarquía de Three.js, conservando los materiales originales.
El empaquetador copia ambos módulos junto al GLB para poder importarlos desde un visor con módulos ES.
El nodo `autobus_bronco` incluye en `userData.movimiento` radios, posiciones de ejes y límites de conducción.

```js
import { AutobusAnimado } from './autobus_animado.mjs';

const gltf = await loader.loadAsync('./autobus_bronco.glb');
escena.add(gltf.scene);
const autobus = new AutobusAnimado(gltf.scene);
autobus.teletransportar({ x: 20, y: alturaCalzada, z: -10, rumbo: 0 }, true);
autobus.entrada({ velocidad: 3, direccion: 0.12 }); // m/s, radianes; positivo = izquierda
// En el bucle de la ciudad, con dt en segundos:
autobus.actualizar(dt);
// Para frenar suavemente:
autobus.entrada({ velocidad: 0, direccion: 0 });
```

Para una ruta que ya proporciona distancias/curvatura, usar `avanzarDistancia(ds, k)` en lugar de `actualizar(dt)`:
`ds` es el arco firmado del centro del eje trasero, en metros, y `k` su curvatura firmada en 1/m.
No usar ambos métodos para el mismo avance. `teletransportar(pose)` coloca el vehículo sin rodar las ruedas;
con segundo argumento `true` también reinicia su fase. El controlador trabaja en las coordenadas del padre del modelo,
que debe tener escala unitaria. El eje vertical y el ajuste a pendientes/colisiones se conectan al sistema de calzada
durante la integración; este controlador es cinemático sobre un plano.

El controlador escribe los pivotes directamente: no reproducir a la vez los clips con `AnimationMixer`.
Los clips se incluyen para vistas previas y motores que requieran animaciones. En recta, la velocidad del clip es
`abs(velocidad) / (2 * Math.PI * radio)`; en curvas, usar el controlador para respetar las distancias de cada rueda.
En Blender las pistas NLA permiten inspeccionar ambos sentidos por separado.
