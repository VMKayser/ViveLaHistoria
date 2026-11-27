# Guía y Plan Estratégico: Proyecto Mi Ciudad Charcas (Sucre 3D)

Bienvenido a la carpeta de documentación estratégica y técnica para el desarrollo y presentación del proyecto **Mi Ciudad Charcas / Sucre 3D** (Hackathon American Spaces CBA).

Esta carpeta contiene la documentación integral elaborada a partir del análisis exhaustivo del repositorio maestro `miCiudadCharcas`.

---

## Documentos Disponibles

### 1. [ESTRUCTURA_PROYECTO.md](file:///c:/Users/antra/Desktop/Hacka_American_Spaces(CBA)/Mi_Ciudad_Sucre/guia/ESTRUCTURA_PROYECTO.md)
**Estructura y Arquitectura Técnica del Proyecto:**
- Resumen ejecutivo del gemelo digital de Sucre (Charcas).
- Diagrama de flujo e interacción de subsistemas (Mermaid).
- Desglose detallado por módulos:
  - `ciudad3d/` (Motor Godot 4.7, Wasm, shaders, tráfico físico `VehicleBody3D`, cámaras peatonales a 1.6m).
  - `web/` (Next.js 15, React, interfaz interactiva, puente `MotorGodot.ts` $\leftrightarrow$ `puente.gd`, visualizador `/mapa` y `/estilos`).
  - `blender/` (Pipeline de calidad automatizada con `calidad.py`, ingesta de datos OSM y topografía).
  - `contenido/` (Patrimonio histórico de 1809, personajes célebres, escape rooms y saberes patrimoniales).
  - `coordinacion/` (Partición de manzanas urbanas M001-M065, registro de tareas Norte/Sur y optimización de draw calls).
- Convenciones métricas y estándares de rendimiento (presupuesto < 250 draw calls, 60 FPS estables).

---

### 2. [PLAN_DE_TRABAJO_6_HORAS.md](file:///c:/Users/antra/Desktop/Hacka_American_Spaces(CBA)/Mi_Ciudad_Sucre/guia/PLAN_DE_TRABAJO_6_HORAS.md)
**Plan de Trabajo Intensivo de 6 Horas (Sprint Hackathon):**
- **Hora 1 (00:00 - 01:00):** Diagnóstico, Entorno y Puesta en Marcha (`localhost:3000`, canvas 3D y WebAssembly).
- **Hora 2 (01:00 - 02:00):** Auditoría de Calidad 3D y Optimización de la Zona Cero (`calidad.py = 0`, Plaza 25 de Mayo, Casa de la Libertad).
- **Hora 3 (02:00 - 03:00):** Activación de la "Ciudad Viva" (Líneas de microbuses de Sucre, peatones, ciclo día/noche colonial).
- **Hora 4 (03:00 - 04:00):** Gamificación e Integración Histórica (Puntos de interés interactivos, modales en React, personaje histórico y trivia patrimonial).
- **Hora 5 (04:00 - 05:00):** Empaquetado, Rendimiento y Pruebas Multiplataforma (Build de producción, controles táctiles y fallback offline).
- **Hora 6 (05:00 - 06:00):** Pulido Visual, Ruta Demostrativa ("Golden Path" de 2 min) y Estructura del Pitch para el Jurado.
- Matriz de roles y responsabilidades.
- Matriz de mitigación de riesgos técnicos.
- Checklist de verificación final.
