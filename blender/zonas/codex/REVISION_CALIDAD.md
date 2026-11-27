# Revisión de calidad de la mitad Codex · 2026-11-13

## Alcance

42 GLB (41 manzanas y P01), 874.369 triángulos. A–C se modelaron por inventario fotográfico y funciones por edificio; las fachadas siguen los lados reales de las huellas recortadas. Inventarios: `INVENTARIO_PLAZA.md` e `INVENTARIO_JUNIN.md` e `INVENTARIO_DALENCE.md`.

- Plaza: R0013–R0024. Aguja y remate M053, balcones y arco M057, Hotel Plaza y árbol M059, USFX M058/M065, esquina M064. Todas resueltas con nota y hash.
- Junín/Arenales: R0025 y R0034–R0037. Rectorado M037 y frente M027 con templo, espadaña y atrio calado. R0026–R0033 las asumió Claude en AMP_O (#12/#13); no se tocó su geometría.
- Dalence: R0080–R0086, Asamblea de tres plantas, patio abierto con pabellón curvo y edificio de ventanales largos/mansarda. Dos postes y seis cables conectados, comprobados por rayos. Afinado por revisión cruzada #20.
- Mínimo sin foto: 28 manzanas genéricas y cuerpos no documentados de M037/M055/M058/M059/M061/M064/M065. 97 casas en 35 manzanas: vanos con rejas, acceso, zócalo, carpintería, cornisa/alero y cubierta de teja. Cinco caracteres deterministas; colores y composición son aproximados. M063 conserva las medianeras del cuerpo posterior del museo: cubierta y remates, 1.622 triángulos; su fachada documentada está en M061.
- Materiales por rol, sin recursos externos nuevos. No se modificaron kit, BASE, visor ni modelos de Claude.

## Comprobaciones reproducibles

Desde la raíz del repositorio:

```sh
python3 blender/zonas/codex/auditar_modelos.py
python3 blender/zonas/codex/auditar_minimo.py
~/apps/blender-5.2.3-linux-x64/blender --background --python blender/zonas/codex/auditoria_calles.py -- codex
~/apps/blender-5.2.3-linux-x64/blender --background --python blender/zonas/codex/auditar_contactos.py
~/apps/blender-5.2.3-linux-x64/blender --background --python blender/zonas/codex/recorrer_codex.py -- --detalles
python3 blender/zonas/codex/mosaicos_revision.py
```

`auditoria_calles.py` ejecuta el auditor común de Claude en lectura y cierra Blender limpiamente. El informe común conserva avisos `FLOTA` en cornisas, aleros y apliques que un único rayo vertical no reconoce como apoyados. El segundo pase suelda costuras de normales y busca contacto con otras islas del mismo edificio, incluidos apoyos laterales. Umbral de revisión: 8,5 cm; no constituye una simulación estructural ni prueba todos los solapamientos. Los cables y la vegetación requieren además revisión visual.

`recorrer_codex.py` carga ambos agentes como contexto, conserva las cámaras a 1,6 m —vereda real para frentes de calle y patio para huellas interiores— y las huellas SHA-256 de los 42 modelos. M063 es el cuerpo posterior del museo: sus dos vistas de calle muestran el acceso del conjunto en M061 y una toma oblicua adicional comprueba su cubierta; no se inventa fachada en medianeras.

`--manzanas=M060 --actualizar` repite solo las vistas de una manzana modificada y conserva las demás. Cada toma guarda el hash de su modelo principal, los hashes del contexto y su inicio de revisión. `mosaicos_revision.py` exige cobertura de todos los modelos, imágenes posteriores a su revisión y que el modelo principal de cada toma corresponda al GLB actual. Esto permite afinar una manzana sin repetir todas las demás; el contexto histórico de cada toma queda registrado. Las comparaciones fotográficas de B/C se conservaron por separado; este recorrido comprueba el último lote y los encuentros a pie.

## Resultado final

- Integridad, ids, roles y presupuestos: correctos en los 42 modelos. Total bajo el límite de 1,5 millones; casas bajo 15.000 triángulos y monumentos bajo 60.000 por objeto.
- Auditor común: **0 invasiones de calzada**, 48 muestras de faroles válidos en vereda. Los avisos de piezas elevadas se contrastaron en el segundo pase. No se afirma que el auditor común dé cero avisos.
- Segundo pase: **0 piezas sin contacto cercano**; se corrigieron previamente 22 separaciones de campanas/yugos y ornamentos. Informe `revisiones/codex/auditoria_D/contactos.json`.
- Recorrido: **87/87 imágenes validadas y examinadas en ocho mosaicos**, 86 a 1,6 m y una cubierta oblicua de M063. Corregidos los encuadres ocultos M058/M063/M070 y el escorzo de M061.
- Observaciones posteriores de Claude #22–#26: huecos del perímetro P01, nave de San Miguel, mobiliario/fachada de Junín oeste y azoteas M055. **Pendientes de corregir**; un pase de contacto o invasiones no prueba cobertura del suelo ni parecido fotográfico.

Informes e imágenes locales en `revisiones/codex/repaso_20261113/`, `revisiones/codex/dalence/` y mosaicos en `revisiones/codex/calidad_E/`, no versionados. Auditoría completa tras el afinado, con revalidación adicional de M060 al ajustar la cúpula.

## Límites

Las alturas se estiman desde las fotos; los interiores y frentes sin foto son aproximaciones coloniales. El recorrido usa render de geometría con contexto; las texturas pintadas por rol las aplica el visor. Las esculturas de P01 siguen siendo siluetas estilizadas. No se atribuye exactitud documental a las casas sin foto ni a los patios que no se ven en referencias.

## Cambios posteriores al corte de Dalence

- P01 #23: 181.889 rayos, cero huecos, cero calzada, contacto cero y cuatro vistas de borde examinadas. Commit `6363767`.
- M037 #24: nave sobre Arenales, cuatro referencias y seis vistas a pie; cero calzada, contacto cero. Commit `7fafe4c`.
- M055: eliminada casa genérica E749b6b por indicación del usuario, suelo institucional y cubiertas de Catedral. Diagnóstico revela 194 intercepciones del relleno de BASE ante las fachadas. **Pendiente limpieza de BASE por Claude y validación con contexto real regenerado.**
- Integridad actual: 42 modelos, 885,676 triángulos; 96 casas sin foto. No se confunde la revisión diagnóstica sin relleno con una corrección ya publicada de BASE.

## Corte tras Junín oeste #22

42 GLB, 891.148 triángulos, 96 casas sin foto. Recorrido actual: 100/100
imágenes (99 a 1,6 m), nueve mosaicos con hashes/fechas comprobados.
M037: cota del convento corregida desde su calle y vanos/zócalo accesibles;
M027 conserva su frente fotográfico. Cuatro postes, siete faroles y doce
vanos libres por BVH. Auditor global: 0 calzada, 53 muestras de mobiliario
en vereda, 771 avisos elevados; segundo pase 0 separaciones >8,5 cm.
Informes `repaso_20261113/auditoria_actual.txt` y `contactos_actuales.json`.
La limpieza de BASE ante Catedral/Gobernación sigue pendiente de Claude.
