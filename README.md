# Vive la Historia · Casa de la Libertad

Juego educativo en primera persona sobre la historia de la **Casa de la Libertad** (Sucre, Bolivia).
El jugador recorre la Sala Mayor en 1825, cumple misiones, toma decisiones y descubre lo que realmente pasó.
**Cada dato histórico del juego se muestra en una ficha con su fuente**, priorizando fuentes oficiales.

Hackathon Regional 2026 · Sede Sucre · Sector Patrimonio y educación.

## Estado

| Parte | Estado |
| --- | --- |
| Escena 1: La Asamblea de 1825 | Jugable de inicio a fin, con arquitectura de Blender, texturas PBR y luz horneada |
| Sistema de fuentes y fichas | Listo: 10 fuentes (5 oficiales), 20 fichas |
| Escenas 2 (Juana Azurduy, 1816) y 3 (Universidad, 1809) | Fichas cargadas; jugabilidad pendiente |
| Personajes y brazos del jugador | Provisionales (cápsulas); listos para recibir los modelos del equipo |
| Diálogo libre con IA (RAG) | Pendiente |

## Cómo ejecutarlo

Requisitos: [Godot 4.7](https://godotengine.org/download) con plantillas de exportación.

```bash
# Abrir en el editor
godot --path juego --editor

# Jugar directamente
godot --path juego

# Exportar a web y probar en el navegador
godot --headless --path juego --export-release "Web" ../build/web/index.html
python3 -m http.server 8060 -d build/web
# abrir http://localhost:8060
```

Controles: `WASD` moverse · `Shift` correr · `Espacio` saltar · `E` usar · `R` inspeccionar lo que tienes en la mano · `Tab` diario de fichas y fuentes · clic para controlar la cámara · `Esc` libera el ratón.

## Pruebas

```bash
# Valida fuentes, fichas y escenas (sale con código 1 si hay errores)
godot --headless --path juego --script res://tests/validar_datos.gd

# Recorre la Escena 1 completa simulando al jugador (29 comprobaciones, incluida la colisión del piso)
godot --headless --path juego res://tests/prueba_flujo.tscn
```

## Política de fuentes

1. El juego **solo muestra datos históricos que están en `juego/data/fichas.json`**. Los diálogos son recreaciones y lo indican en pantalla; el dato histórico va en la ficha.
2. Cada ficha cita al menos una fuente de `juego/data/fuentes.json`, con institución, URL y fecha de consulta.
3. Tipos de fuente, en orden de prioridad: `oficial` (la Casa de la Libertad y su Fundación Cultural del BCB, organismos públicos), `prensa`, `academica`, `enciclopedia`.
4. Si dos fuentes no coinciden, la ficha se marca `fuentes_difieren` y explica la diferencia. **No elegimos una versión en silencio.**
5. Lo que solo tiene respaldo de una enciclopedia queda `por_verificar` hasta encontrar una fuente oficial.
6. Cada ficha tiene un campo `revision` que completa un docente o curador. El juego muestra "Revisión docente pendiente" hasta que se aprueba.
7. `cita` guarda el texto literal de la fuente principal para que cualquiera pueda comprobarlo.

### Agregar una ficha

```json
{
  "id": "f_ejemplo",
  "escenas": ["asamblea_1825"],
  "titulo": "Título corto",
  "texto": "El dato, en una o dos frases, fiel a la fuente.",
  "cita": "Texto literal de la fuente (opcional).",
  "estado": "verificada",
  "fuentes": ["cdl_historia"],
  "revision": {"aprobada": false, "revisor": "", "fecha": ""}
}
```

Luego corre `validar_datos.gd`: avisa si la ficha cita una fuente que no existe o le falta algún campo.

## Estructura

```
blender/
  construir_casa_libertad.py  arquitectura, horneado con Cycles y exportación .glb
  casa_libertad.blend         escena para seguir modelando
herramientas/                 descarga de recursos, generador del nivel, optimización web
juego/
  assets/                     texturas, muebles, cielo, retrato, arquitectura (ver LICENCIAS.md)
  materiales/                 materiales PBR (.tres)
  shaders/                    shader de arquitectura con luz horneada
  data/
    fuentes.json            catálogo de fuentes (oficiales primero)
    fichas.json             datos históricos, cada uno con sus fuentes
    escenas/asamblea_1825.json   misiones, personajes, diálogos y decisiones
  escenas/
    jugador.tscn            controlador en primera persona con mano visible
    niveles/asamblea_1825.tscn   nivel de la Sala Mayor y el patio (generado por herramientas/generar_nivel.py)
  scripts/
    autoload/               Controles, Fuentes (repositorio), EstadoJuego (eventos)
    jugador/                movimiento, salto, carrera, mano, interacción
    interaccion/            objetos que se toman, se observan, personajes, zonas, entregas
    arquitectura/           arcadas, repetidor (vigas, sillas, barandas) y materiales horneados
    misiones/               gestor de misiones y validador de escenas
    ui/                     HUD, fichas con fuentes, diálogos, decisiones, diario
  tests/                    validación de datos y prueba de flujo completo
```

Las escenas son **data-driven**: misiones, diálogos y decisiones se editan en el JSON sin tocar código.

## Gráficos

El renderizador web de Godot (*Compatibility*, WebGL 2) no calcula luz rebotada. Por eso la iluminación global se hornea en Blender con Cycles y Godot la combina con el sol en tiempo real.

```
herramientas/descargar_assets.py   →  juego/assets/  (texturas PBR, muebles, cielo HDRI, retrato; CC0 o dominio público)
blender/construir_casa_libertad.py →  juego/assets/arquitectura/casa_libertad.glb + luz_horneada.png
herramientas/generar_nivel.py      →  juego/escenas/niveles/asamblea_1825.tscn
herramientas/optimizar_importacion.py → compresión de GPU y mipmaps para web
```

| Capa | Cómo se logra |
| --- | --- |
| Arquitectura (patio, claustro con arcos, galería, Sala Mayor, artesonado, coro) | Una sola malla de Blender con colisión: 1.110 vértices y 10 materiales (unas 10 llamadas de dibujo) |
| Luz del cielo, rebotes del sol y velas | Horneada con Cycles (GPU OptiX, unos 35 s) en un mapa de 2048 px |
| Sol, sombras de personajes y relieve | En tiempo real en Godot (`juego/shaders/arquitectura_horneada.gdshader`) |
| Texturas | PBR de Poly Haven a escala real, proyección triplanar en coordenadas de mundo |
| Muebles | Sillas talladas, solio, mesas, candelabros, arañas, puertas, faroles y macetas de Poly Haven |
| Exportación web | De 130 MB a 47 MB con compresión S3TC/BC5/BC7, mipmaps y límites de resolución |

**Rehacer la arquitectura y la luz** (tras cambiar `blender/construir_casa_libertad.py`):

```bash
blender -b --factory-startup --python blender/construir_casa_libertad.py
python3 herramientas/optimizar_importacion.py
godot --headless --path juego --import
```

Las coordenadas de `construir_casa_libertad.py` y `generar_nivel.py` son las mismas. Si se mueve un muro en uno, hay que moverlo en el otro. `generar_nivel.py` reescribe la escena completa, así que no conviene correrlo si alguien editó el `.tscn` a mano.

**Capturas para revisar los gráficos:** `godot --path juego res://tests/capturas.tscn` abre una ventana unos segundos y guarda 6 vistas en `build/capturas/`.

### Integrar modelos propios de Blender

1. Exporta en glTF (`.glb`) dentro de `juego/assets/modelos/<nombre>/`.
2. **Personajes:** en el nodo del personaje (`Personajes/Serrano`, etc.), asigna el `.glb` a la propiedad `modelo`. Reemplaza la cápsula provisional y reproduce en bucle la animación `idle` si existe.
3. **Brazos del jugador:** reemplaza `BrazoProvisional` dentro de `escenas/jugador.tscn`.
4. **Objetos:** arrástralo como hijo del objeto y borra el nodo `Modelo`. Si no tiene `CollisionShape3D`, se crea una caja que envuelve todo el modelo.
5. Agrega cada recurso con su autor y licencia a `juego/assets/LICENCIAS.md`.
