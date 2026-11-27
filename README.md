# Vive la Historia · Casa de la Libertad

Juego educativo en primera persona sobre la historia de la **Casa de la Libertad** (Sucre, Bolivia).
El jugador recorre la Sala Mayor en 1825, cumple misiones, toma decisiones y descubre lo que realmente pasó.
**Cada dato histórico del juego se muestra en una ficha con su fuente**, priorizando fuentes oficiales.

Hackathon Regional 2026 · Sede Sucre · Sector Patrimonio y educación.

## Estado

| Parte | Estado |
| --- | --- |
| Escena 1: La Asamblea de 1825 | Jugable de inicio a fin en *greybox* (bloques provisionales) |
| Sistema de fuentes y fichas | Listo: 10 fuentes (5 oficiales), 20 fichas |
| Escenas 2 (Juana Azurduy, 1816) y 3 (Universidad, 1809) | Fichas cargadas; jugabilidad pendiente |
| Modelos 3D realistas (Blender) | En curso, a cargo del equipo de modelado |
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

# Recorre la Escena 1 completa simulando al jugador (28 comprobaciones)
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
juego/
  data/
    fuentes.json            catálogo de fuentes (oficiales primero)
    fichas.json             datos históricos, cada uno con sus fuentes
    escenas/asamblea_1825.json   misiones, personajes, diálogos y decisiones
  escenas/
    jugador.tscn            controlador en primera persona con mano visible
    niveles/asamblea_1825.tscn   nivel greybox de la Sala Mayor y el patio
  scripts/
    autoload/               Controles, Fuentes (repositorio), EstadoJuego (eventos)
    jugador/                movimiento, salto, carrera, mano, interacción
    interaccion/            objetos que se toman, se observan, personajes, zonas, entregas
    misiones/               gestor de misiones y validador de escenas
    ui/                     HUD, fichas con fuentes, diálogos, decisiones, diario
  tests/                    validación de datos y prueba de flujo completo
```

Las escenas son **data-driven**: misiones, diálogos y decisiones se editan en el JSON sin tocar código.

## Integrar modelos de Blender

1. Exporta en glTF (`.glb`) y copia el archivo dentro de `juego/modelos/`.
2. En el nivel, arrastra el `.glb` como hijo del objeto o personaje que reemplaza y borra el nodo `Modelo` provisional.
3. Si el nodo no tiene `CollisionShape3D`, el script crea una caja de colisión a partir del modelo.
4. Para el entorno, reemplaza los nodos de `Geometria` por el modelo de la sala con colisión (en Blender, sufijo `-col` en las mallas de colisión).
5. Anota la licencia de cada modelo descargado en `juego/modelos/LICENCIAS.md`.

Renderizado: la exportación web usa el renderizador *Compatibility* (WebGL 2). El realismo depende sobre todo de texturas PBR, iluminación horneada (*lightmaps*) y buena exposición.
