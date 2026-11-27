# Museo Interior — Casa de la Libertad (1809)

Reconstrucción 3D optimizada para **Blender 5.2** y **Godot 4.7 (`gl_compatibility` / WebGL sin hilos)** de la **Casa de la Libertad** (antigua Capilla Doméstica y Aula Magna de la Universidad Mayor, Real y Pontificia de San Francisco Xavier de Chuquisaca) en Sucre, Bolivia.

---

## 1. Qué se construyó

### Modelo 3D procedural y texturas (`museo_interior/`)
Todo el edificio se genera por código en Python (`bpy` / `bmesh`) dentro de [`blender/casa_libertad_1809.py`](blender/casa_libertad_1809.py) a partir de las fotografías y capturas ubicadas en `referencias/casa_libertad/` y `referencias/imagenes/`:

- **Fachada exterior colonial (`22.00 m` de frente):**
  - Portada barroca tallada con columnas pareadas, entablamento, roleos, pináculos en jarrón, ventana alta con reja, medallón central y Escudo de San Francisco Xavier.
  - Material dedicado **`piedra_fachada`** (arenisca marrón-ocre oscura envejecida con sillares marcados) en portada, zócalo y marcos de las 4 ventanas bajas, contrastando con el estuco blanco cal (`muro`), vidrio oscuro profundo tras rejas y puertas, balcones corridos de madera cálida sobre ménsulas oscuras, acera gris pizarra (`vereda_gris`) y portón de cedro tachonado en bronce.
- **Zaguán y Claustro Principal (`22.00 × 22.00 m`):**
  - Patio central de `14.40 × 14.40 m` con empedrado colonial en rombos, 5 arcos de medio punto por lado sobre columnas de arenisca clara (`piedra`), fuente ochavada central con agua, faroles emisivos, bancas, macetas, ventana con reja hacia el salón y la escultura en bronce de *El Flechero* (`2,100` triángulos).
  - Puertas cerradas con reseña en el ala oeste (Sala Virreinal, Salón de Honor y Biblioteca).
- **Salón de la Independencia (`9.20 × 24.00 m` interiores):**
  - Artesonado colonial, coro dorado, arañas de cristal con velas emisivas, sillería modular instanciada, presidio elevado, vitrina del Acta de la Independencia (6 de agosto de 1825) y testero histórico con Bolívar al centro, Sucre y Ballivián a los costados, retratos superiores y urnas de las espadas.
- **Ala museográfica este conectada en recorrido continuo:**
  - **Sala de los Guerrilleros:** acceso abierto desde el Salón por puerta verde calada, cofre de Juana Azurduy de Padilla, vitrina transparente (Alpha simple sin refracción `Transmission`) con cañón histórico de montaña, cuadros al óleo y Templete de la Bandera de Belgrano.
  - **Pasillo del Águila:** vigas verde colonial en pendiente, retratos enmarcados y pedestal central con águila tallada.
  - **Sala de Bolívar:** tarima escalonada, busto escultórico de Simón Bolívar (`1,048` triángulos) sobre pedestal de piedra con detalles dorados, Escudo Nacional de Bolivia en medallón limpio, 4 estandartes históricos (Wiphala, Tricolor boliviana, Bandera de Belgrano y punzó), vitrinas y 6 retratos laterales con placa.

### Presupuesto WebGL y exportación (`exports/casa_libertad.glb`)
- **Archivo exportado:** [`exports/casa_libertad.glb`](exports/casa_libertad.glb) (`6,124,128` bytes ≈ **`5.84 MiB`**, formato glTF 2.0 binario Y-Up con texturas empaquetadas).
- **Geometría:** `172` objetos (`24` mallas únicas compartidas), **`41,846` triángulos visibles + `960` triángulos `-colonly` = `42,806` triángulos totales**, escala uniforme `1.0` (`scale_err = 0.0000`).
- **Materiales (`10` en total, `Transmission = False`):**
  - `8` materiales PBR 512×512 (`muro`, `piedra`, `piedra_fachada`, `madera`, `teja`, `piso`, `hierro`, `oro_bronce`) con mapas `_albedo.jpg`, `_normal.jpg`, `_roughness.jpg` generados por [`blender/generar_texturas_pbr.py`](blender/generar_texturas_pbr.py).
  - `1` texture atlas 1024×1024 (`atlas_museo`) con emisivo (`_emit.png`), roughness y normal generados por [`blender/generar_atlas.py`](blender/generar_atlas.py).
  - `1` material de vidrio ligero (`vidrio_vitrina`, Alpha Blend).
- **Colisiones y marcadores embebidos en el `.glb`:**
  - `3` cuerpos simplificados invisibles con sufijo `-colonly` (`CL_Col_Pisos-colonly`, `CL_Col_Muros-colonly`, `CL_Col_Mobiliario-colonly`), convertidos automáticamente por Godot en `StaticBody3D` (`layer = 1`, escala `1.0`).
  - `5` marcadores `LUZ_*` (`LUZ_ZAGUAN_01`, `LUZ_SALON_ARANA_01`, `LUZ_SALON_ARANA_02`, `LUZ_SALA_GUERRILLEROS`, `LUZ_SALA_BOLIVAR`).
  - `14` marcadores interactivos `POI_*` (`POI_ENTRADA_PORTON`, `POI_PATIO_FUENTE`, `POI_ESTATUA`, `POI_PORTADA_SALON`, `POI_ACTA_INDEPENDENCIA`, `POI_PRESIDIO_BOLIVAR`, `POI_SALA_MUSEO`, `POI_CANON`, `POI_BANDERA_BELGRANO`, `POI_PASILLO_AGUILA`, `POI_SALA_BOLIVAR`, `POI_SALA_VIRREINAL`, `POI_SALA_HONOR`, `POI_BIBLIOTECA`).

### Integración en Godot 4.7 (`ciudad3d/escenas_historicas/casa_libertad/`)
Se dejó una carpeta modular lista dentro del proyecto Godot siguiendo la convención de `ciudad3d/escenas_historicas/`:
- `casa_libertad.glb` (+ texturas `.ctex` reimportadas con compresión VRAM S3TC/BPTC + ETC2/ASTC).
- `casa_libertad.tscn` + `casa_libertad.gd` (`CasaLibertadMuseo`):
  - Coloca hasta **5 `OmniLight3D`** cálidas en los `LUZ_*` (con `distance_fade` a 55 m y sin sombras por defecto en WebGL Compatibility).
  - Configura **`VisibilityRange`** (`40–64 m`) en **73 mallas** interiores y mobiliario para ocultarse automáticamente cuando el jugador camina lejos por la Plaza 25 de Mayo.
  - Conecta los **14 `POI_*`** mediante `Area3D` (`collision_mask = 8`) al autoload `Interaccion` (`ciudad3d/scripts/interaccion.gd`), mostrando un banner de proximidad y fichas históricas al pulsar `E` (o `Enter` / clic).
- `recorrido_casa_libertad.tscn` + `recorrido_casa_libertad.gd`: escena autónoma en primera persona para recorrer directamente todo el museo sin necesitar descargar teselas de toda la ciudad.
- `portal_plaza.gd` (`PortalCasaLibertad`): puente listo para colocar un disparador frente a la portada en Plaza 25 de Mayo y entrar/salir al museo.

---

## 2. Estructura de carpetas

```text
museo_interior/
├── README.md
├── ayudas/
│   └── instrucciones.md
├── blender/
│   ├── generar_texturas_pbr.py     # Genera los 24 mapas PBR 512x512 en texturas/pbr/
│   ├── generar_atlas.py            # Genera atlas_museo.png + _emit/_rough/_normal
│   ├── casa_libertad_1809.py       # Script principal bpy (fachada, claustro, salas, -colonly, GLB)
│   └── mcp_cliente.py              # Cliente socket para ejecutar scripts en Blender abierto
├── exports/
│   └── casa_libertad.glb           # Modelo glTF 2.0 final (5.84 MiB)
├── referencias/
│   ├── casa_libertad/              # Fotografias reales del museo
│   └── imagenes/                   # Capturas del video institucional y guia.md
├── renders/                        # Renders de revision Blender EEVEE y capturas Godot Compatibility
└── texturas/
    ├── atlas_museo*.png
    └── pbr/*.jpg
```

Y su contraparte lista en Godot:

```text
ciudad3d/escenas_historicas/casa_libertad/
├── casa_libertad.glb
├── casa_libertad.tscn
├── casa_libertad.gd
├── recorrido_casa_libertad.tscn
├── recorrido_casa_libertad.gd
└── portal_plaza.gd
```

---

## 3. Cómo verlo y cómo usarlo

### A. Recorrerlo ahora mismo en Godot 4.7 (Escritorio — modo Compatibility)
Ejecuta desde la raíz del repositorio (`miCiudadCharcas/`):

```powershell
& "C:\Users\antra\Documents\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --path "ciudad3d" --rendering-method gl_compatibility --resolution 1280x720 "res://escenas_historicas/casa_libertad/recorrido_casa_libertad.tscn"
```

**Controles dentro del recorrido:**
- `W A S D` o **Flechas arriba/abajo**: caminar.
- `Shift`: correr.
- **Arrastrar ratón** (botón izquierdo) o `Q` / **Flechas izq./der.**: girar la cámara (`R` / `F` cabeceo).
- `E` (o `Enter` / botón en pantalla): abrir y cerrar la ficha histórica al acercarte a cualquier punto `POI_*` (cuando estás fuera de un `POI_*`, `E` conserva su giro a la derecha normal).
- `N` (o botón superior derecho): alternar **Día → Atardecer → Noche → Amanecer**.
- `Esc`: cerrar la ficha abierta.

### B. Regenerar texturas o el `.glb` desde Blender + MCP
1. Si modificas texturas:
   ```powershell
   python "museo_interior\blender\generar_texturas_pbr.py"
   python "museo_interior\blender\generar_atlas.py"
   ```
2. Con Blender 5.2 abierto y el addon **Blender MCP** conectado en `localhost:9876`:
   ```powershell
   python "museo_interior\blender\mcp_cliente.py" run "museo_interior\blender\casa_libertad_1809.py" --export
   ```
   *(Opcional: agrega `--render` para regenerar las vistas en `museo_interior/renders/`).*
3. Para actualizar el `.glb` en Godot: copia `museo_interior\exports\casa_libertad.glb` a `ciudad3d\escenas_historicas\casa_libertad\casa_libertad.glb` y corre:
   ```powershell
   & "C:\Users\antra\Documents\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path "ciudad3d" --import --quit
   ```

### C. Verlo en navegador (`http://localhost:8060`, WebGL sin hilos)
*(En este equipo aún no están instaladas las plantillas de exportación `4.7.2.stable` ni `ciudad3d/export_presets.cfg`, por eso se describe aquí el procedimiento para cuando quieras probarlo en web):*
1. En el Editor de Godot 4.7.2: **Editor → Administrar plantillas de exportación → Descargar e instalar** para `4.7.2.stable`.
2. Copia `ciudad3d/export_presets.ejemplo.cfg` como `ciudad3d/export_presets.cfg` (verifica en `[preset.1.options]` que `variant/thread_support=false`).
3. Si deseas probar **solo el museo sin descargar toda la ciudad**, define temporalmente como escena principal `res://escenas_historicas/casa_libertad/recorrido_casa_libertad.tscn` en `project.godot` (o exporta con los `datos/` completos de la ciudad).
4. Exporta y sirve en el puerto `8060`:
   ```powershell
   New-Item -ItemType Directory -Force -Path "museo_interior\web_test" | Out-Null
   & "C:\Users\antra\Documents\Downloads\Godot_v4.7.2-stable_win64.exe\Godot_v4.7.2-stable_win64_console.exe" --headless --path "ciudad3d" --export-release "Web" "..\museo_interior\web_test\index.html"
   python -m http.server 8060 -d "museo_interior\web_test"
   ```
   Abre **`http://localhost:8060`** en el navegador.

---

## 4. ¿Se puede conectar este museo con la ciudad de Sucre de tu compañero (Rua) y entrar?

**Sí, es completamente posible.** El proyecto Godot (`ciudad3d/`) ya está diseñado para acoplar escenas nuevas mediante `ciudad3d/escenas_historicas/` y el autoload `Interaccion` (`ciudad3d/scripts/interaccion.gd`).

### Punto técnico clave antes de unirlos
En la ciudad actual de Sucre (`ciudad3d/herramientas/empaquetar.py`), las manzanas modeladas en Blender (como `web/public/models/ciudad/codex/M037.glb` y `web/public/models/ciudad/claude/S_PLAZA25.glb`) se empaquetan por teselas de 100 m (`t_-3_1_b.bin` / `t_-3_2_b.bin`) generando **una caja cerrada sólida con colisión (`ConcavePolygonShape3D`)** en el lote `Ee30c62` (`SP25_casa_libertad`). Además:
- En `S_PLAZA25`, el frente asignado a Casa de la Libertad mide **`15.76 m`** (`tramo s = 30..45.76`), junto al edificio de bandas rojizas (`s = 17..30`).
- Este modelo interior completo mide **`22.00 m`** de ancho por **`56.15 m`** de profundidad.

Por ese motivo hay **dos formas reales de conectarlo** según lo que decidan con tu compañero:

---

### Opción A (Recomendada): Entrada por portal desde la Plaza 25 de Mayo
Es la forma más limpia, **no requiere modificar las mallas de tus compañeros**, evita choques con los muros sólidos de `M037.glb`/`S_PLAZA25.glb` y mantiene el presupuesto WebGL al mínimo al no cargar los muebles interiores junto con toda la ciudad.

**Pasos para unirlo con el proyecto de tu compañero:**
1. **Generar los datos de la ciudad (si aún no están en `ciudad3d/datos/`):**
   Tu compañero (o el equipo en una máquina con los archivos fuente de `web/public/mapa/raw/lienzo.glb` y los `.glb` de `web/public/models/ciudad/`) ejecuta:
   ```bash
   python3 ciudad3d/herramientas/empaquetar.py
   node ciudad3d/herramientas/vehiculos.mjs
   ```
2. **Asegurar la posición exacta del portal en `ciudad3d/scripts/principal.gd`:**
   - Ya existe el script `ciudad3d/escenas_historicas/casa_libertad/portal_plaza.gd` (`PortalCasaLibertad`), que coloca un `Area3D` justo frente a la puerta de Casa de la Libertad en la vereda de la Plaza 25 de Mayo:
     - Base de fachada calculada sobre `S_PLAZA25.glb`: **`POSICION_PLAZA_25 = Vector3(-233.5396, 62.18, 167.4812)`**
     - Orientación hacia la Plaza: **`ROTACION_Y_PLAZA_25 = 0.89151 rad`** (`51.08°`)
     - Punto del portal sobre la vereda (`+2.1 m` hacia la plaza): **`(-231.91, 63.38, 168.80)`**
   - Si tu compañero actualiza el mapa o mueve la acera de `M037`, basta ajustar `POSICION_PLAZA_25` y `ROTACION_Y_PLAZA_25` en `casa_libertad.gd`.
3. **Conectar la transición en `principal.gd` y probar ida y vuelta:**
   - Verificar que `principal.gd` instancie `PortalCasaLibertad` (ya preparado en el hook de `principal.gd`, junto con el flag de retorno `retorno_plaza_casa_libertad`).
   - El jugador camina por la Plaza 25 de Mayo → se acerca a la puerta de la Casa de la Libertad → ve `"Casa de la Libertad · Presiona [E] para entrar al museo"` → pulsa `E` (o `Intro`) → hace fundido (`ui.fundir`) hacia `recorrido_casa_libertad.tscn` → recorre el museo y sus `14 POI_*` → al volver por el portón exterior o presionar `B`, regresa automáticamente a la vereda de la Plaza mirando hacia la plaza.
4. **Si en Web usan el HUD de React (`web/src/ciudad/`):**
   - Ten en cuenta que en la web `ui.visible = not Datos.en_web` en `principal.gd`, pero `CasaLibertadHUD` y `PortalCasaLibertad` usan sus propios `CanvasLayer` en capa `15`, por lo que los avisos de `[E]` y tarjetas históricas también se ven encima del lienzo web sin romper la UI de React. Solo revisen en `web/src/ciudad/motor/MotorGodot.ts` / `puente.gd` que las teclas (`E` / `B`) no queden interceptadas cuando el usuario enfoque el `<canvas>`.

---

### Opción B (Alternativa): Encastre físico directo dentro de la manzana `M037` (entrar caminando sin pantalla de transición)
Si con tu compañero deciden que se pueda cruzar el portón caminando directamente desde la calle sin cambiar de escena:

**Pasos que deberán seguir juntos en Blender + Godot:**
1. **Coordinación de propiedad en `reparto/manzanas.json` y `AGENTS.md`:**
   - Pedir permiso / traspaso en `coordinacion/` con el dueño de `M037` (`codex`) y `S_PLAZA25` (`claude`), ya que `AGENTS.md` prohíbe editar manzanas ajenas sin acuerdo explícito.
2. **Abrir el hueco en la fachada y vaciar el volumen en Blender:**
   - En `blender/secciones/plaza_25_mayo_frentes.py` (`frente_libertad`, tramo `s = 30..45.76`): retirar `SP25_casa_libertad` o recortar el bloque sólido en ese tramo (ajustando también el frente vecino `17..30` si se decide respetar los `22.00 m` reales o escalar/recortar el ancho lateral).
   - En `blender/zonas/codex/M037.py` (`Ee30c62`): retirar la caja sólida `cuerpo(e, 8.3)` detrás de la fachada para que la colisión de `M037.glb` no tapone el zaguán, el claustro ni el Salón (`56.15 m` de fondo).
   - Re-exportar `S_PLAZA25.glb` y `M037.glb` y volver a correr `python3 ciudad3d/herramientas/empaquetar.py`.
3. **Instanciar `casa_libertad.tscn` en las coordenadas de la Plaza:**
   - En `principal.gd` (o en una escena de edificios históricos cargada junto a `Ciudad`), instanciar `res://escenas_historicas/casa_libertad/casa_libertad.tscn` aplicando su transform alineado:
     ```gdscript
     var museo := preload("res://escenas_historicas/casa_libertad/casa_libertad.tscn").instantiate()
     museo.transform = CasaLibertadMuseo.transform_en_plaza_25()
     add_child(museo)
     ```
   - Esto ya deja `visibility_range_end` (`40–64 m`) activo para no dibujar muebles ni salas interiores desde lejos.
4. **Ajustar la iluminación combinada (`hora.gd` vs materiales PBR estándar):**
   - **Importante:** en la ciudad abierta, `ciudad3d/scripts/hora.gd` configura `entorno.ambient_light_source = Environment.AMBIENT_SOURCE_DISABLED` porque las calles usan el shader personalizado `estilo.gdshaderinc` en lugar de `StandardMaterial3D`.
   - Al meter `casa_libertad.glb` dentro de `principal.tscn` sin entorno propio, los `StandardMaterial3D` interiores recibirán luz únicamente de las `5 OmniLight3D` (`LUZ_*`) y de los emisivos; si el claustro o algún muro interior se viera muy oscuro en las zonas sin `OmniLight3D`, conviene subir ligeramente la energía/rango de las 5 `OmniLight3D` en `casa_libertad.gd` o habilitar una luz ambiente hemisférica suave solo al entrar al recinto (para no alterar el aspecto de las calles).
5. **Reempaquetar y probar exportación Web/APK:**
   - Verificar que `casa_libertad.glb` quede incluido en el `.pck` (`export_presets.cfg`, no excluido por `exclude_filter`) y compilar con:
     ```bash
     cd web && npm run ciudad
     ```
   - Recorrer en escritorio y en navegador confirmando: ingreso libre por el portón sin pared invisible, FPS estables > 30 en Plaza 25 de Mayo y lectura de los `14 POI_*` con `E`.
