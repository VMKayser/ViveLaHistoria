# Correcciones del usuario (modo revisión del visor)

El usuario (o un revisor) recorre la ciudad en el visor, activa **Revisión** (tecla V), **enmarca** con el mouse la
zona mal modelada (tecla B) y deja un comentario obligatorio, una categoría, una prioridad y, si quiere, una foto de
referencia y fotos del proyecto tomadas cerca. El servidor local guarda cada corrección aquí:

```
coordinacion/revisiones/R0007/
  revision.json    datos (ver abajo)
  recorte.jpg      solo lo enmarcado
  captura.jpg      pantalla completa con el marco en rojo (para ubicarse)
  referencia.jpg   foto adjunta por el revisor (si la hay)
```

## Qué significa una corrección (aclaración del usuario, 2026-11-12)

La corrección se guarda en el **punto donde estaba parado el revisor** (`escena.camara`: posición, rumbo,
inclinación). Quiere decir: **desde esta posición, la ciudad debería verse como en `referencia.jpg`, o más o
menos**. Pasar de la foto real a la escena virtual admite ajustes de encuadre y de vista: no se busca coincidencia al
milímetro, sino que desde ahí se reconozca el lugar (edificios, alturas, vanos, árboles, anchos de calle). El
`centro` y la `manzana` que se calculan son solo una pista de qué edificio se miraba. En el visor, el alfiler
numerado aparece en esa posición de la cámara.

## Cómo trabajarlas (agentes)

1. Al empezar cada sesión: `python3 scripts/revisiones.py <agente>` lista las pendientes asignadas a ti, con las
   rutas de las imágenes y una línea `camaras_extra=[...]` para reproducir la toma con `revisar()`.
   **Mira siempre `recorte.jpg`, `captura.jpg` y `referencia.jpg`** antes de corregir.
2. Al tomar una: en SU `revision.json` pon `"estado": "en_curso"`.
3. Al terminar: `"estado": "resuelta"` y
   `"resolucion": {"agente": "<agente>", "fecha": "AAAA-MM-DD", "nota": "qué se cambió", "commit": "<hash>"}`.
   Si no corresponde (ya estaba bien, es del otro agente…): `"estado": "descartada"` con la razón en `nota`.
4. Commitea la carpeta de la corrección (`coordinacion/revisiones/R0007`) junto con tu manzana.

Cada corrección tiene UN agente (`lugar.asignado`, calculado con `reparto/manzanas.json`): solo ese la edita.
Las que quedan sin asignar (`asignado: null`, fuera del reparto) las revisa claude y, si son de codex, cambia
`asignado` y le avisa por `mensajes_claude.md`. Si una corrección cae en tu reparto pero es del otro (p. ej. una
fachada que el lienzo asignó mal), cámbiale `asignado` y avísale.

## revision.json

| campo | qué es |
|---|---|
| `id`, `creada`, `autor` | número correlativo, fecha ISO, nombre del revisor |
| `estado` | `pendiente` → `en_curso` → `resuelta` / `descartada` |
| `categoria` | `fachada`, `techo`, `volumen`, `piso`, `mobiliario`, `vegetacion`, `falta`, `sobra`, `otro` |
| `prioridad` | `alta`, `media`, `baja` |
| `comentario` | lo que está mal o cómo arreglarlo (obligatorio) |
| `lugar` | `manzana`, `edificio` (id de la huella del lienzo), `espacio` (`P01`, `BASE`), `asignado`, `lat`, `lon` |
| `escena.camara` | ojos en metros del lienzo (`lienzo.x/y/z`, X este, Y norte, Z altura), `rumbo_grados` (0 = norte, 90 = este), `inclinacion_grados`, `fov_vertical_grados`, `aspecto`, `modo` (`peaton` o `mapa`) |
| `escena.marco` | rectángulo en pantalla, 0–1 desde arriba a la izquierda |
| `escena.centro` | punto 3D (lienzo) que se ve en el centro del marco; `esquinas` = los 4 vértices (null = cielo) |
| `escena.distancia_m`, `escena.calle` | distancia de la cámara al centro, calle más cercana |
| `archivos` | `recorte`, `captura`, `referencia` (o null), `fotos_proyecto` (nombres en `fotos/`) |
| `resolucion` | null hasta que el agente la resuelve |
