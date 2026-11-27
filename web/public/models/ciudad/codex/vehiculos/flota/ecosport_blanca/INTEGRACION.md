# Flota de vehículos · Mi Ciudad

Los seis vehículos se entregan por separado en esta carpeta con `.glb`, `.blend` y `.ficha.json`. `catalogo.json` enumera los modelos, sus archivos y sus dimensiones estimadas. El autobús y sus variantes siguen en la carpeta superior.

Abrir `index.html` a través del servidor HTTP del proyecto:

```text
http://localhost:3000/models/ciudad/codex/vehiculos/flota/index.html
```

El visor permite elegir modelo, mirar seis vistas, comparar con el diseño, ver la malla y descargar los archivos. **Probar marcha** hace una curva de demostración. W/A/S/D o flechas y los controles táctiles permiten conducir; espacio o **Frenar** detienen gradualmente; **Reiniciar** repone la pose y las ruedas. El deslizador fija la velocidad de avance/demostración en km/h. Esta escena de prueba es independiente de la ciudad.

## Archivos y coordenadas

| ID / raíz | Vehículo |
| --- | --- |
| `vagoneta_blanca` | Vagoneta blanca clásica |
| `montero_sport_blanca` | Mitsubishi Montero Sport blanca |
| `ecosport_blanca` | Ford EcoSport blanca |
| `hilux_blanca` | Toyota Hilux blanca doble cabina |
| `toyota_roja` | Toyota clásica roja de cabina extendida |
| `ford_azul` | Camioneta Ford azul oscuro/gris |

Unidades: metros y segundos. Blender: X delante, Y izquierda, Z arriba. GLB/Three: X delante, Y arriba, Z derecha. El origen queda a ras del suelo y en el centro longitudinal del cuerpo. Anchura del catálogo corresponde a carrocería; espejos y accesorios amplían los límites. Consultar la ficha para los límites reales exportados.

La raíz, cuyo nombre es el ID, contiene `userData.movimiento`: radio, ejes, semivía y límites de conducción. Cada rueda tiene un pivote en su eje, con los mismos nombres que BRONCO: `rueda_trasera_derecha`, `rueda_trasera_izquierda`, `rueda_delantera_derecha`, `rueda_delantera_izquierda`. Delante, cada rueda es hija de `direccion_delantera_derecha/izquierda`. El repuesto de la EcoSport permanece fijo en su portón.

## Cargar y mover en Three.js

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VehiculoAnimado } from '../autobus_animado.mjs';

const id = 'hilux_blanca';
const gltf = await new GLTFLoader().loadAsync(`${id}.glb`);
escena.add(gltf.scene);
const vehiculo = new VehiculoAnimado(gltf.scene, id);

// Velocidad en m/s; dirección en radianes. 10 km/h = 10 / 3.6 m/s.
vehiculo.entrada({ velocidad: 10 / 3.6, direccion: 0.15 });
// En el bucle, dt en segundos: acelera y frena suavemente.
vehiculo.actualizar(dt);

// Frenar; las ruedas dejan de girar cuando el vehículo se detiene.
vehiculo.entrada({ velocidad: 0, direccion: 0 });
// Recolocar sin rodadura ficticia. y fija la altura del origen en el mundo.
vehiculo.teletransportar({ x: 15, y: alturaCalzada, z: -20, rumbo: 0.4 }, true);
```

`VehiculoAnimado` reutiliza el adaptador BRONCO con raíz configurable y la misma `CinematicaVehiculo`; no duplica sus fórmulas. Cambiar los límites por instancia pasando una configuración completa en el tercer argumento:

```js
const raiz = gltf.scene.getObjectByName(id);
const config = { ...raiz.userData.movimiento,
  velocidad_maxima: 20 / 3.6, aceleracion: 1.2, frenada: 3.0 };
const vehiculo = new VehiculoAnimado(gltf.scene, id, config);
```

`velocidad_maxima`, `retroceso_maximo`: m/s; `aceleracion`, `frenada`: m/s²; `direccion_maxima`: radianes; `rapidez_direccion`: radianes/s. Para convertir una velocidad km/h a m/s, dividir por 3,6. La dirección se limita a valores compatibles con la batalla y la vía del vehículo.

Si una ruta controla el recorrido, usar `avanzarDistancia(ds, curvatura)` en lugar de `actualizar(dt)` para ese avance. `ds` es distancia firmada en metros del centro del eje trasero, curvatura en 1/m. No aplicar además una traslación y animación de ruedas independientes. Ackermann y las distancias distintas de las cuatro ruedas ya se calculan dentro del controlador.

Los clips `rodar_adelante` y `rodar_atras` dan una vuelta por segundo y sirven como demostración aislada. No ejecutar un `AnimationMixer` sobre los mismos pivotes cuando se usa el controlador por distancia.

## Instancias, materiales y rendimiento

Clonar la jerarquía para cada vehículo: cada instancia necesita pivotes y controlador propios. Las mallas y materiales pueden compartirse si no se recolorean; clonar materiales antes de cambiar pinturas. No unir ruedas con carrocería, aplicar transformaciones a los pivotes ni fusionarlos con los lotes estáticos de edificios. Mantener una raíz de vehículo sin escala no uniforme ni un padre rotado; el controlador usa X/Z del plano de su padre.

Los GLB contienen materiales PBR y normal de goma empaquetado. El normal Rubber004 es CC0, ya registrado en `recursos/LICENCIAS.md` para el autobús. Las piezas se agrupan por material y pivote; la ficha registra triángulos y mallas. El presupuesto de esta primera entrega es 95.000 triángulos por vehículo; probar cantidades simultáneas en el celular antes de desplegar tráfico. Las láminas de `referencias/` sirven solo para el visor; no se necesitan para cargar el GLB.

## Fuentes y regeneración

Las fuentes están en `blender/zonas/codex/vehiculos/flota/`. `disenos.json` enlaza los seis juegos de datos de diseño y `construir.py` llama a su constructor. La Montero Sport, la EcoSport y la Hilux describen perfiles, ventanas, ejes y elementos de identidad en sus propios JSON. Comparten las operaciones geométricas de `carroceria_moderna.py`. Sus constructores definen las tomas, ópticas, defensas y accesorios de cada lámina. `taller_lamina.py` reúne la prueba de holgura, el rig, la exportación y el estudio.

```bash
# Un modelo, con sus seis cámaras de revisión:
~/apps/blender-5.2.3-linux-x64/blender -b -t 2 \
  -P blender/zonas/codex/vehiculos/flota/construir.py -- hilux_blanca

# Todos de forma secuencial; nunca seis Blender simultáneos:
python3 blender/zonas/codex/vehiculos/flota/generar_todos.py

# Empaquetar visor, catálogo, referencias y documentación pública:
node blender/zonas/codex/vehiculos/flota/preparar_visor.cjs
# Pasar un ID para generar solo su visor individual.

# Validar los GLB reales y su contrato de ruedas/clips:
node blender/zonas/codex/vehiculos/flota/validar.cjs
```

Los renders NVIDIA quedan en `revisiones/codex/flota/<id>/`. `--sin-render` omite imágenes; `--vistas=perspectiva,lateral` limita las cámaras. Los recursos se empaquetan en el Blender y en el GLB según corresponda; los archivos finales funcionan sin las rutas locales del agente.

## Límites de esta entrega

Diseños estilizados desde fotos/láminas, con escala estimada; partes ocultas e interior interpretados. Puertas cerradas, sin apertura animada. El controlador trabaja sobre un plano: faltan rutas, ajuste de altura y orientación a las pendientes, tráfico y colisiones de la ciudad. La incorporación al visor urbano se hace preservando este contrato y atendiendo el terreno del proyecto. No aplicar `calidad.py` de manzanas a estos vehículos sin emplazamiento.
