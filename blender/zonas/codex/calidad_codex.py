"""Ejecuta el control común sin dejar Blender esperando al audio al cerrar.

Uso con ejecutar.py: calidad_codex.py -- codex M037
"""
import os
import runpy

runpy.run_path(os.path.abspath(os.path.join(os.path.dirname(__file__),'../../kit/calidad.py')),
              run_name='__main__')
