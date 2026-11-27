# Compatibilidad comprobada el 2026-11-11

- [Referencia de edición](https://developers.openai.com/api/reference/resources/images/methods/edit): `POST /v1/images/edits` admite múltiples entradas. El original se envía primero; las referencias después.
- [Guía oficial](https://developers.openai.com/api/docs/guides/image-generation): `gpt-image-2` procesa todas las entradas con alta fidelidad; omitir `input_fidelity`. Se usan `quality=high`, `size=auto`, `n=1`, `output_format=png`. `auto` no garantiza las dimensiones exactas del original.

Se elige `gpt-image-2` por compatibilidad con la CLI instalada de imagegen. La documentación también enumera modelos posteriores Sunburst/Flare; no se afirma que este sea el más reciente. No se sabe qué modelo o configuración produjo los ejemplos del usuario en ChatGPT y no se promete reproducirlos exactamente.

La CLI usa el SDK oficial `openai` y decodifica `b64_json`. El wrapper normaliza formato y orientación EXIF a PNG temporal, sin filtros ni reescalado de salidas. Cada entrada normalizada debe pesar menos de 50 MB. Las llamadas y las referencias tienen coste de API independiente del uso de la herramienta integrada en Codex.
