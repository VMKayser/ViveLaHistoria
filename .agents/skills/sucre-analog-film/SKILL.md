---
name: sucre-analog-film
description: Editar carpetas de fotografías con estética cinematográfica analógica de Sucre, indie de los 70 y Kodak Portra 400, mediante edición OpenAI y referencias visuales comunes. Usar para procesar SucreAesthetic o colecciones similares conservando las escenas y guardando copias en generadas/.
---

# Sucre Analog Film

Transformar la estética mediante edición generativa conservando fielmente la escena. No prometer identidad exacta de píxeles o arquitectura ni resultados idénticos a ChatGPT: la generación puede alterar detalles y necesita revisión visual.

## Dentro de Codex

Usar `image_gen` por defecto; no requiere clave API. Consultar la skill `imagegen` del entorno si está disponible. El script prepara y registra el lote; Codex ejecuta cada edición con la herramienta integrada.

1. Desde la raíz del proyecto, ejecutar:

   ```bash
   python3 .agents/skills/sucre-analog-film/scripts/procesar.py plan SucreAesthetic
   ```

   Valida JPG, JPEG, PNG, WEBP, TIFF y BMP y escribe `generadas/plan.json`. `--recursivo` incluye subcarpetas. Excluye `generadas/`, enlaces simbólicos y referencias del lote. Usa por defecto las imágenes de la carpeta hermana `SucreAestheticAplied`. Para otra referencia, añadir `--referencia /ruta/ejemplo.png` (repetible) y mantener esos mismos argumentos en todos los comandos.

2. Cargar las referencias y cada original con `view_image`. Para cada trabajo `pendiente`, llamar a `image_gen` con el original primero y las mismas referencias después. Usar completo [assets/prompt.txt](assets/prompt.txt), también incluido en el plan. Solo la primera imagen aporta contenido. Una llamada por foto, sin collages ni referencias cambiantes tomadas de resultados nuevos. No sustituir por filtros locales.

3. Guardar inmediatamente la salida:

   ```bash
   python3 .agents/skills/sucre-analog-film/scripts/procesar.py registrar SucreAesthetic \
     --origen SucreAesthetic/foto.jpg --resultado /ruta/devuelta/por/image_gen.png
   ```

   Produce `generadas/foto.jpg.png` y su JSON con prompt, referencias, hashes y dimensiones. La extensión original evita colisiones JPG/WEBP. No modifica originales ni sobrescribe salidas. Reejecutar `plan` permite reanudar. Cambios en originales, referencias, prompt o salida producen `conflicto`: conservar la versión anterior aparte antes de reprocesar.

4. Comparar cada salida con su original: encuadre, proporción, perspectiva, ventanas, torres, personas, cables, letreros y cielo. Marcar `revision_visual` en su JSON como `revisada` o `requiere_correccion`, con una nota concreta. No aprobar automáticamente por color o hashes. Ante desviaciones, informar y hacer como máximo una corrección dirigida desde el original, conservando la primera salida. Detenerse si persisten. No recortar ni estirar para ocultar cambios.

## API autónoma

Vía disponible cuando el usuario pide API/CLI, como en la creación de esta skill. Usa la CLI instalada de `imagegen`, sin modificarla ni crear un SDK alternativo. Requiere Python 3.11+, Pillow, `openai`, `OPENAI_API_KEY` local y acceso a la API. No pedir claves por chat.

```bash
# Ver peticiones sin red ni consumo:
python3 .agents/skills/sucre-analog-film/scripts/procesar.py api SucreAesthetic --simular
# Todas las pendientes con las dos referencias predeterminadas:
python3 .agents/skills/sucre-analog-film/scripts/procesar.py api SucreAesthetic
# Prueba de una foto con una referencia elegida:
python3 .agents/skills/sucre-analog-film/scripts/procesar.py api /ruta/fotos \
  --referencia /ruta/ejemplo.png --limite 1
```

Instalar dependencias en el entorno elegido con `python3 -m pip install openai Pillow`. La CLI se busca en `CODEX_HOME` o `~/.codex`; se puede indicar `IMAGE_GEN_CLI`. Se usa `gpt-image-2`, calidad `high`, tamaño `auto`, PNG y `n=1`, sin `input_fidelity` (alta fidelidad automática). `--calidad` cambia la calidad explícitamente. La API tiene facturación y acceso propios. Un error detiene el lote conservando lo terminado; no repetir a ciegas tras un timeout. El SDK puede reintentar errores transitorios según su configuración predeterminada.

Consultar [references/api.md](references/api.md) al revisar compatibilidad. No cambiar modelo silenciosamente. Un script de terminal no puede invocar `image_gen`: esa modalidad la ejecuta Codex siguiendo el plan.
