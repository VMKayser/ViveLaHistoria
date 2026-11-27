#!/bin/sh
# Abre una sección en Blender (con interfaz, en la NVIDIA) y conecta el MCP. Uso: scripts/abrir_seccion.sh plaza_25_mayo
cd "$(dirname "$0")/.." || exit 1
__NV_PRIME_RENDER_OFFLOAD=1 __GLX_VENDOR_LIBRARY_NAME=nvidia exec ~/apps/blender-5.2.3-linux-x64/blender \
  -P blender/secciones/abrir_en_blender.py -- "${1:-plaza_25_mayo}"
