# Ciudad 3D (Godot 4.7)

La ciudad virtual de Sucre es **un solo proyecto Godot** que se exporta a dos lados:

| destino | renderizador | datos de la ciudad | comando (desde `web/`) |
|---|---|---|---|
| **Web** (solo PC: `/ciudad`, dentro de la página React) | Compatibility (WebGL 2), sin hilos | se descargan a demanda de `web/public/ciudad3d/datos/` | `npm run ciudad` |
| **APK** Android (celular y tableta: la web los manda a instalarla) | Mobile (Vulkan) | dentro del paquete | `npm run ciudad:apk` |

Desde el 2026-11-25 reemplaza al visor three.js (plan en `coordinacion/PLAN_GODOT.md`).

## Cómo se arma

```
web/public/models/ciudad/<agente>/*.glb ──► herramientas/empaquetar.py ──► datos/ (teselas de 100 m por rol, faroles,
web/public/mapa/ (lienzo, calles, cerros)                                         calles, índice ciudad.json)
web/public/trafico/*.glb + red.json ──────► herramientas/vehiculos.mjs ──► datos/vehiculos/, red.json
                                              herramientas/exportar.mjs ──► web/public/ciudad3d/ (wasm, pck, datos/)
                                                                         └► movil/build/MiCiudad-Sucre.apk
```

- `npm run ciudad`: empaqueta (incremental, solo lo que cambió), convierte los vehículos, importa y exporta la web. Después
  basta recargar http://localhost:3000/ciudad.
- `npm run ciudad:apk`: lo mismo para el APK (firmado con `movil/claves/`; copia a `web/public/descargas/` si existe).
- `npm run ciudad:minimapa`: vuelve a fotografiar la ciudad desde arriba para el minimapa (`texturas/minimapa.webp`,
  ~10 min; hacerlo cuando cambie mucho la ciudad).
- `export_presets.cfg` **no se versiona** (lleva la contraseña de la llave del APK): se arma copiando
  `export_presets.ejemplo.cfg` y completando `keystore/release*` con la llave de `movil/claves/`. Presets: `Android` (incluye
  `datos/*`) y `Web` (excluye `datos/*` y `herramientas/*`; plantillas sin hilos).
- Godot: `~/apps/godot/Godot_v4.7.2-stable_linux.x86_64` (o la variable `GODOT`), con las plantillas de exportación 4.7.2.

## Estructura

| | |
|---|---|
| `scripts/principal.gd` | arranque, modos (inicio girando → a pie), hora del día, guardado de la posición, banderas de prueba |
| `scripts/ciudad.gd`, `tesela.gd` | carga por teselas alrededor del caminante (hilos en el APK/escritorio, presupuesto de 7 ms por cuadro en la web), colisión solo a < 170 m |
| `scripts/estilo.gd`, `shaders/estilo*.gdshader(inc)`, `shaders/luz.gdshaderinc`, `texturas/estilo.json` | el estilo: un solo shader para ciudad, copas, cerros y vehículos (abajo), relieve y brillo por material, detalle por zona, vidrios por edificio, faroles de noche, niebla |
| `shaders/hojas.gdshader`, `texturas/hojas.png` (`herramientas/hojas_textura.py`) | racimos de hojas de las copas (abajo) |
| `scripts/pasto.gd`, `shaders/pasto.gdshader` | pasto y flores sembrados de cerca (abajo) |
| `scripts/oclusion.gd`, `shaders/oclusion.gdshader` | oclusión ambiental en pantalla (abajo) |
| `scripts/hora.gd` (autoload `Hora`) | día, atardecer, noche, amanecer: cielo, sol, luz, niebla, faroles |
| `scripts/post.gd`, `shaders/post_*.gdshader` | enfoque adaptativo (o el filtro Kuwahara, apagado), color (vibrancia, tono dividido, curva en S en sRGB), viñeta y FXAA |
| `scripts/calidad.gd` | niveles alta/media/baja y bajada automática (`?calidad=`, `?sin=sombra,post,trafico,ao,pasto,hojas` para medir) |
| `scripts/jugador.gd`, `ui.gd`, `minimapa.gd`, `calles.gd` | caminante (teclado, ratón, joystick táctil), interfaz del APK |
| `scripts/trafico.gd`, `scripts/trafico/` | tráfico con física real (abajo) |
| `scripts/puente.gd`, `revision.gd` | puente con la página web: eventos `sucre` y `window.sucreGodot` (abajo) |
| `scripts/datos.gd` (autoload `Datos`) | lee `res://datos/` o, en la web, los descarga (`?v=` huella para la caché) |
| `scripts/guardado.gd` (autoload `Guardado`), `scripts/interaccion.gd` (autoload `Interaccion`) | lo guardado y las zonas interactivas para lo que viene |
| `personajes/`, `vehiculos/`, `escenas_historicas/`, `escape_rooms/` | lugar para lo nuevo (cada carpeta dice cómo engancharse) |
| `herramientas/` | empaquetador, vehículos, exportar, captura con Chrome sin ventana (`captura_web.mjs`) |

## Rendimiento: una tesela, pocas llamadas de dibujo

En WebGL lo que cuesta es la cantidad de llamadas de dibujo, no los triángulos. Por eso el empaquetador junta en **una
superficie** todo lo de una tesela que comparte grupo (suelo sin sombra · sólido · liviano sin choque), clase de material
(normal · fondo para los cerros, que solo cambia `sin_niebla`) y origen (claude · codex · lienzo · volúmenes); cada vértice
lleva el número de su rol en `UV.x`. Las copas ya no tienen material de doble cara: el empaquetador duplica sus caras con
la normal invertida y `UV.y = 1`. El shader (`estilo.gdshaderinc`, único; los vehículos lo usan con `movil = true`) toma
de tres arreglos los parámetros de ese rol, y las texturas de relieve y de detalle son `Texture2DArray` (`texturas/capas_*.png`, se rehacen con
`python3 herramientas/capas_textura.py` si cambian `relieve` o `detalle` en `texturas/estilo.json`).

Medido el 2026-11-26 (vista de la Plaza 25 de Mayo, escritorio): 742 → 241 llamadas por cuadro con la misma imagen
(PSNR 44 dB); memoria del proceso 293 → 177 MB (la colisión ya no guarda mallas en la tarjeta de vídeo). En la web, con
tráfico y oclusión: 60 fps de mediana y ~135 llamadas (antes 52–56 fps y ~718 llamadas, sin oclusión). Se probó y se
descartó la compresión de vértices de Godot: ahorra ~30 % de vídeo pero cambia los vidrios.

## Carga en la web (qué cuesta y cómo se acortó)

Medido el 2026-11-26 en Chrome sin ventana, carga en frío hasta el evento `lista` (`detail.segundos` trae el tiempo del
motor): **31 s → 17 s** (misma build sin la precompilación: 26 s; Godot esperaba 8,2 s enlazando shaders, con ella 0,16 s;
`?sin_precompilar` la apaga para comparar). Antes eran 31 s, de los que ≈15 s eran **enlazar programas de shader** (Godot Compatibility compila cada variante al
primer uso y espera el resultado en el hilo principal: pausas de 1–5 s), ≈4 s descargas y arranque del wasm y el resto
armar teselas y su colisión mientras se dibujaba la ciudad girando detrás de una pantalla opaca. En la segunda visita
Chrome ya tiene los programas en su caché y baja a ≈12 s. Lo que se hizo:

- **Precompilación desde la página** (`web/src/ciudad/motor/precompilar.ts`): mientras baja el wasm, un contexto WebGL
  aparte enlaza en paralelo (KHR_parallel_shader_compile) los mismos programas que pedirá Godot, sacados de
  `web/public/ciudad3d/shaders.json`. La caché de programas es del navegador: cuando Godot los pide ya están. La lista la
  genera `herramientas/capturar_shaders.mjs` (Chrome sin ventana sobre `sucre.html`); `exportar.mjs` la rehace sola cuando
  cambia la huella de `shaders/`, `scripts/`, `project.godot` o Godot (`--sin-shaders` la salta).
- **Menos shaders**: un solo shader de estilo para ciudad, copas, cerros y vehículos (cada shader distinto son 4 variantes
  más que compilar).
- **Mientras carga no se dibuja de verdad**: la pantalla de inicio tapa el lienzo, así que se dibuja a escala 0,25 (los
  mismos shaders, que así se compilan antes de entrar) y las teselas tienen 30 ms por cuadro en vez de 7
  (`Ciudad.presupuesto_ms`). `Calidad` no mide ni baja de nivel hasta aparecer a pie (antes la carga lenta la bajaba a
  "media" y obligaba a recompilar el filtro).
- **Colisión sin malla intermedia**: `Tesela.forma()` desindexa y usa `set_faces` (~10 ms) en vez de ArrayMesh +
  `create_trimesh_shape` (35–105 ms: en WebGL sube la malla a la GPU y la vuelve a leer).
- **Lo que no hace falta para entrar, después**: los vehículos (≈5 MB) se descargan al aparecer a pie
  (`Trafico.arrancar()`), todos a la vez; la página pide el minimapa (2,2 MB) y el catálogo del taller al estar lista.

## Salto de calidad visual (2026-11-26)

Pedido del usuario: "aprovechar Godot… colores, texturas, iluminación… pasto, flores, árboles más realistas, sin perder
fluidez". Lo que cambió:

- **Luz** (`shaders/luz.gdshaderinc`, común a la ciudad y al pasto): sol cálido + cielo azul hemisférico + rebote cálido del
  suelo, terminador algo pintado y una curva de tonos que solo comprime las luces altas. Antes eran tres franjas con 1,8:1
  entre sol y sombra (todo lavado y lavanda); ahora ≈3:1, sombras frescas y luces cálidas como `estilo/referencia_estilo.png`.
  Los valores por hora están en `scripts/hora.gd` (`"luz"`).
- **Relieve real de las texturas**: la textura de detalle y la de relieve (en grises) se usan como altura y la normal se
  inclina por derivadas en pantalla (sin tangentes ni UV), de cerca. Metros de relieve y brillo del sol por rol:
  `texturas/estilo.json` → `rugosidad` y `brillo`. Vehículos: pintura con barniz que refleja la calle (fresnel).
- **Cielo de día** azul limpio con las mismas nubes del sky_97 (`recursos/cielos_finales.py → dia_azul`); bruma azulada.
- **Imagen final**: el Kuwahara quedó apagado en todos los niveles (borroneaba las texturas y costaba 3–4 fps en la web); lo
  reemplaza un enfoque adaptativo (CAS), vibrancia, luces cálidas/sombras frescas y curva en S (`herramientas/generar_post.py`).
- **Copas**: el empaquetador cubre cada copa (componentes conexas de `follaje`/`follaje_claro`) con racimos de hojas: cuadros
  con `texturas/hojas.png` que el shader abre hacia la cámara (en el pase de sombras, hacia el sol: sombras moteadas) y mece
  con el viento; normal esférica de la copa. Van en archivos `t_*_h.bin` que solo se descargan cerca (`radio_hojas`: 130 m
  en alta, 90 en media, 0 en baja). ~120 000 racimos, 3 MB en total.
- **Pasto y flores**: `datos/pasto.json` (triángulos de césped y de canteros) → `scripts/pasto.gd` siembra matas de hojas de
  pasto y flores en celdas de 16 m como MultiMesh (una llamada por celda), más ralas con la distancia y hundidas en el borde
  (sin saltos). Radio 32 m en alta, 22 en media, nada en baja. Los canteros planos pasan al rol `cantero` (tierra).
- **Tráfico más rápido**: calles a 40–50 km/h y la plaza a 35 (`web/scripts/red_vial.py`), autos 50 km/h, micro 43, clásicos
  41, carrozas 30 (`web/scripts/vehiculos_trafico.json → movimiento`), curvas con 2,4 m/s² laterales. El galope del caballo
  usa una zancada real de 3,4 m (`scripts/trafico/caballo.gd`): ~2 trancos por segundo a 7–8 m/s. El registro
  (`SUCRE_TRAFICO_REGISTRO=1`) da la velocidad media y máxima por tipo: autos 6–8 m/s de media en marcha (picos 10–13),
  carrozas ~6–7 (el caminante corre a 5,5).

Medido el 2026-11-26 en la web (Chrome sin ventana con la GPU, a pie en la Plaza 25 de Mayo, `?calidad=alta`, misma toma):
versión anterior 16–17 fps de mediana (mínimo 14), nueva 16 (mínimo 13–14) con todo lo nuevo encendido. Carga en frío
18,8–20,9 s. `?sin=hojas,pasto,post,ao,sombra,trafico` apaga cada parte; el evento `posicion` trae `gpu_ms` (en WebGL da 0:
el navegador no expone el temporizador).

## Oclusión ambiental

El SSAO de Godot es solo de Forward+; la web (Compatibility) y el APK (Mobile) usan `shaders/oclusion.gdshader`: un
rectángulo a pantalla completa que lee la profundidad, reconstruye posición y normal y mira 12 muestras (8 en media, 0 en
baja) en el hemisferio, con los valores del N8AO de la web anterior (radio 2,5 m a pie y 8 desde el aire, intensidad 2,2,
color #5b5f86; desde el 2026-11-26 una sombra fresca casi neutra). Multiplica la imagen antes de los transparentes; en Mobile compensa que el búfer guarda el color a la mitad.
`SUCRE_AO_DEPURAR=1` la muestra sola.

## Tráfico con física real

Cada bus es un `VehicleBody3D` de 7,5 t con cuatro `VehicleWheel3D` (suspensión, tracción trasera, frenos, dirección) que
rueda sobre la colisión real de la calzada. Un **conductor** (`trafico/vehiculo.gd`) lo maneja: persecución pura sobre su
carril de la red vial, IDM contra el vehículo de adelante, el peatón y las curvas (la aceleración pedida se convierte en
fuerza de motor o de freno), paso por turnos en los cruces, y si se atasca retrocede y vuelve a intentar. Cerca del
caminante (135 m; 90 m en la web) hay física completa, con tope de 20 vehículos (12 en la web y el APK: los más cercanos); los demás
avanzan sobre el carril sin simular ruedas. La flota (30 en calidad alta, 22 en media, 12 en baja; un tercio carrozas y
carruajes a caballo) vive en una burbuja de 260 m alrededor del caminante: el que sale reaparece dentro, fuera de la vista.
`?trafico=N` fija la cantidad. En la web la física corre a 30 Hz con interpolación.

**Plaza 25 de Mayo** (`web/scripts/vehiculos_trafico.json → plaza`, pedido del usuario del 2026-11-26: mucho tránsito): con
el caminante a menos de 520 m, el 85 % de los que reaparecen lo hace en el anillo de la plaza (carriles a < 85 m del
centro); en los cruces cercanos prefieren ×8 seguir por el anillo, y los "de la plaza" que se alejan a más de 170 m,
fuera de la vista, vuelven a aparecer en ella. Medido (escritorio, `SUCRE_TRAFICO_REGISTRO=1`, que imprime el resumen por
tipo): 15–22 vehículos en el anillo, 5–8 a caballo. En la web, a pie en la plaza: 47 fps de mediana (tráfico ≈7 ms,
física ≈15 ms por cuadro).

## Puente con la página web (`web/src/ciudad/motor/MotorGodot.ts`)

- Godot → página: `window` recibe eventos `sucre` con `detail.tipo`: `cargada`, `progreso` (fracción), `lista`,
  `posicion` (cada 0,5 s: x, y, z, rumbo, inclinación, fps, llamadas, triángulos, calidad, calle, tiempos), `hora`,
  `captura` (revisiones), `elegida` (clic en una marca de revisión).
- Página → Godot: `window.sucreGodot.entrar() · ir(x, z) · toma(x, y, z, rumbo, incl) · capturar(x0, y0, x1, y1) ·
  marcas(json) · origen(nombre, visible) · calidad(nivel) · hora() · pausar(sí)`.
- La interfaz web (marca, calle, minimapa, ayuda, Día/Noche, revisiones V/B, taller T) sigue siendo React, encima del
  lienzo. Con `?embebido` (la portada) carga a escondidas, deja de dibujar al estar lista y espera `entrar`.

## Probar sin navegador (escritorio)

```
cd ciudad3d
SUCRE_TOMA="-205,64.39,150,-135,0" SUCRE_CAPTURA=/tmp/a.png SUCRE_ESPERA=8 \
  __NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia \
  ~/apps/godot/Godot_v4.7.2-stable_linux.x86_64 --path . --rendering-method gl_compatibility --resolution 1280x720
```
La captura imprime además llamadas, objetos, triángulos y memoria del cuadro; la toma se mantiene hasta capturar.
Otras banderas: `SUCRE_SIN=ao,post,sombra,trafico`, `SUCRE_HORA=noche`, `SUCRE_ANDAR=1`, `SUCRE_TRAFICO=16`, `SUCRE_TRAFICO_REGISTRO=1` (estado de la flota),
`SUCRE_TRAFICO_MIRAR="8,1.6"` (cámara junto al bus más cercano). En la web: `node ciudad3d/herramientas/captura_web.mjs
--url "http://localhost:3000/ciudad?escritorio" --gpu --salida a.png` (Chrome propio sin ventana, no toca el del usuario).
