# Carruajes coloniales de Sucre

El [visor](index.html) permite inspeccionar los tres modelos, enganchar el caballo a cualquiera de los carruajes y probar reposo, paso, galope, reversa y dirección. Los maestros Blender contienen geometría editable, materiales, nodos de enganche, pistas NLA y cámaras de estudio.

| Recurso | GLB | Maestro | Ficha |
| --- | --- | --- | --- |
| Coche colonial cerrado | [GLB](carroza_azul.glb) | [Blender](carroza_azul.blend) | [Ficha](carroza_azul.ficha.json) |
| Carruaje colonial abierto | [GLB](carruaje_madera.glb) | [Blender](carruaje_madera.blend) | [Ficha](carruaje_madera.ficha.json) |
| ROME Galope | [GLB](caballo_rome.glb) | [Blender](caballo_rome.blend) | [Ficha](caballo_rome.ficha.json) |

## Carrozas

Las dimensiones se estimaron de las láminas. El origen está a nivel del suelo. Blender usa +X delante, +Y a la izquierda y +Z arriba. Tras exportar, glTF mantiene +X delante y usa +Y arriba y +Z a la derecha. Cada rueda tiene su propio pivote. Los ejes tienen radios distintos, recogidos en `userData.movimiento.radios_ruedas`.

`tornamesa_delantera` gira la totalidad del eje, incluidas las ballestas delanteras, el balancín y las varas. En el controlador `CarruajeAnimado` de las fuentes, el rumbo se integra a partir de la trayectoria del eje trasero. Cada rueda gira a partir de su arco firmado y de su radio. En las carrozas, el eje de dirección gira alrededor de la tornamesa histórica. Los dos clips portables muestran una vuelta completa de las cuatro ruedas en un segundo, a 24 FPS. Para recorrer una ruta se usa el controlador por distancia.

`varas_caballo` se puede ocultar para visualizar la carroza por sí sola. Los nodos `tirante_derecha/izquierda` están en los extremos del balancín y `vara_punta_derecha/izquierda` marcan el final de las varas. El visor enlaza esos nodos con las hebillas de la pechera y la cincha.

## ROME Galope

El caballo conserva los 984 triángulos facetados y las quince formas del galope original de ROME. La adaptación usa metros, frente +X y cascos a nivel del suelo en reposo. Se añadieron una forma de reposo, un ciclo de paso, la pechera y la cincha con cuatro enganches que acompañan la deformación del tórax. [Créditos y licencia](ROME-ATRIBUCION.md).

| Clip | Duración | Zancada por ciclo |
| --- | ---: | ---: |
| `reposo` | 1 s | 0 m |
| `paso` | 1,25 s | 0,94 m |
| `galope` | 1,5 s | 2,55 m |

La escena permanece en el sitio durante el clip. En el visor, `animarCaballoRome` combina acciones y sincroniza su fase con la distancia firmada. Usa el paso en sentido inverso para la marcha atrás. El montaje coloca la escena completa como hija de `tornamesa_delantera`, suma `avance_desde_lanza_m` a la distancia de enganche de la carroza y usa los nodos `tiro_caballo_*` y `cincha_caballo_*` para los extremos de las correas. Para revisar una acción en Blender, activa las pistas NLA del mismo nombre en las formas del cuerpo, los arreos y los cuatro anclajes.

### Pelajes

El [catálogo](caballo_rome.variantes.json) incluye alazán, castaño, tordo y negro. En el visor se clonan por instancia los dos materiales con `extras.pintura_vehiculo` (`pelaje`, `crin`). Se comparten la geometría, las formas, los clips y los materiales de los cascos, el lucero y los arreos. Cada carroza recuerda su color durante la sesión. Arrancan alazán en la azul y castaño en la de madera.

Las descargas individuales cambian los dos factores de color de material y conservan el bloque binario del maestro.

## Regenerar y verificar

Desde la raíz del repositorio, con los PNG y `caballo_rome_galope_apache2.glb` en `autos/carrozas/`:

```bash
fuentes=blender/zonas/codex/vehiculos/carrozas
publico=web/public/models/ciudad/codex/vehiculos/carrozas
skill=.agents/skills/vehiculo-3d-desde-diseno/scripts
blender_local=~/apps/blender-5.2.3-linux-x64/blender
"$blender_local" -b -t 2 --python-exit-code 1 -P "$fuentes/construir.py"
python3 "$fuentes/preparar_rome.py"
"$blender_local" -b -t 2 --python-exit-code 1 -P "$fuentes/rome_blender.py"
node "$skill/empaquetar_visor.cjs" --entrada "$fuentes/visor.js" --salida "$publico" \
  --copiar "$fuentes/index.html" --copiar "$fuentes/INTEGRACION.md" \
  --copiar "$fuentes/caballo_rome.mjs"
node --test "$fuentes/validacion.test.mjs"
for modelo in carroza_azul carruaje_madera; do
  node "$skill/validar_glb_vehiculo.mjs" --glb "$publico/$modelo.glb" --datos "$fuentes/$modelo.json"
done
for modelo in carroza_azul carruaje_madera; do
  "$blender_local" -b "$publico/$modelo.blend" -t 2 --python-exit-code 1 -P "$fuentes/revisar.py" \
    -- "$modelo" "revisiones/codex/carrozas/$modelo"
done
```

Los recursos están listos para instanciar. La asignación de rutas, la adaptación al terreno y las colisiones con peatones u otros vehículos corresponden al sistema de tráfico urbano. La procedencia de las referencias y las partes interpretadas figuran en `INVENTARIO.md` dentro de las fuentes.
