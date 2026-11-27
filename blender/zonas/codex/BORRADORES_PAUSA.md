# Borradores guardados durante la pausa del 2026-11-12

**Actualización posterior:** M058/M065/M064 ya se integraron y compararon en las fuentes
canónicas `plaza_este.py` y `esquina_audiencia.py`. El generador se unificó en
`casas_codex.py`; estos borradores se conservan como archivo, no se ejecutan.

No están validados ni exportados; no sustituyen las fuentes canónicas.

- `borrador_M058.py`: frente continuo USFX, cinco ejes, miradores extremos,
  balcones, arquivoltas y remates. Usa la franja ausente del lienzo recortada
  a las calles mediante `huella_usfx()`; comprobar continuidad con M057.
- `borrador_M065.py`: ala baja desde USFX hasta el cruce Nicolás Ortiz.
  Comprobar que el recorte deje libre la calzada y encuadrar R0022.
- `borrador_M064.py`: esquina, chaflán apoyado, mirador, balcones,
  mansarda y cúpula. Verificar R0023/R0024 y apoyo de los remates.
- `borrador_generica.py`: propuesta para C. Al retomar, unificar con
  `casas_codex.py`; no hay que mantener dos constructores distintos.

Al retomar: revisar estas fuentes, integrarlas manzana por manzana en su
script canónico, marcar las correcciones en curso y renderizar antes de
exportar. Todos los caminos siguen referidos a la carpeta codex.

Pendiente del mínimo colonial: varias huellas pequeñas de un piso reciben
solo un portón si se calcula un único eje; deben incorporar también vano
con reja cuando la fachada lo permita. Esto afecta a interiores de M059 y
al lote C; no se consideran terminadas por el mero resultado del auditor.

Las referencias y capturas de R0025/R0034/R0035 ya se miraron. R0025 muestra
el Rectorado con portada de esquina, escalinata, ornamentación y tercer
cuerpo posterior: sustituir la casa genérica de E1aa79c, conservando el
resto de M037. R0034/R0035 muestran ventanas y portada barroca de Junín en
Eaeb297; la asignación del lienzo no equivale a una fachada lisa.
