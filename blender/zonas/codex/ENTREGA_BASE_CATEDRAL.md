# Limpieza institucional · comprobación final 2026-11-13

**Borrador histórico: no publicar ni copiar sobre la BASE actual.** Claude
aplicó el parche y publicó BASE. La versión de 13:04, SHA256 `68e01f1bea39f5e91f6da22be95d44533fb352e0410183619449bea06a57aabf`,
da **cero intercepciones** en el sondeo. Las cámaras 130715/130736 con BASE
real fueron repetidas y examinadas: fachadas libres, sin casas añadidas.
El pedido del usuario queda verificado. Los detalles siguientes documentan
la preparación anterior y no autorizan sustituir una BASE más reciente.

## Preparación anterior

El usuario pidió retirar las viviendas genéricas ante Catedral/Gobernación.
Mi M055 ya está corregida en `3e31a4b`. El relleno de BASE aún intercepta 242
rayos delante de las fachadas. No he modificado ni publicado archivos de Claude.

Copia revisable: `revisiones/codex/repaso_20261113/BASE_limpia.glb`.
- Origen SHA256: `56480e798981af735d39badad42288d400d85259b4f300ac898945a6b9cf0d67`.
- Borrador SHA256: `3ebbe6e2d4345ce49b52911e534c40b4035036902803e9908c55eafc918eee21`.
- 635429 triángulos; 11 objetos. 36.254 caras de relleno
  retiradas dentro de la cuadra institucional; otras cuadras conservadas.
- Suelo comprobado con 297.179 rayos: **0 huecos**. Nuevos pavimentos:
  **0 vértices en calzada**. 32 caras pequeñas en encuentros de extremos
  de calzada llevan el rol `calzada`. Informe `cobertura_Catedral_borrador.json`.
- Sondeo del borrador: **0 obstáculos de relleno** ante las fachadas.

Antes de publicar, comparar el hash de BASE actual con el origen: si cambió,
NO sustituirlo por esta copia. Regenerar desde la BASE más reciente con
`borrador_base_catedral.py`, luego auditor de cobertura y
`cerrar_suelo_base_borrador.py` si quedan encuentros abiertos. El parche
`propuesta_base_catedral.patch` reserva la cuadra en el generador para que
no reaparezcan las viviendas. El dueño de BASE debe aplicar/revisar el cambio,
exportar y actualizar su manifiesto. Volver a revisar con BASE real tras publicar.

Las tres vistas anteriores en `M055_base_borrador/` acreditan las fachadas
libres; preceden al cierre de siete encuentros de suelo. No son una prueba de
publicación. Ningún recurso externo añadido.
