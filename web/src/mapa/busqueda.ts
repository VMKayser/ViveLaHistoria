// Búsqueda rápida de la calle y los lugares más cercanos a un punto (coordenadas del mapa en metros).
import type { Calle, LugarOSM } from "./tipos";

const CELDA = 40;

type Tramo = { ax: number; ay: number; bx: number; by: number; nombre: string; tipo: string };

function distTramo(px: number, py: number, t: Tramo) {
  const dx = t.bx - t.ax, dy = t.by - t.ay;
  const l2 = dx * dx + dy * dy || 1;
  const u = Math.max(0, Math.min(1, ((px - t.ax) * dx + (py - t.ay) * dy) / l2));
  return Math.hypot(px - (t.ax + u * dx), py - (t.ay + u * dy));
}

export class Buscador {
  private celdas = new Map<string, Tramo[]>();

  private lugares: LugarOSM[];

  constructor(calles: Calle[], lugares: LugarOSM[]) {
    // la ciudad o el departamento entero no sirven como referencia de cercanía
    this.lugares = lugares.filter((l) => !/^place=(city|town|state|country)/.test(l.tipo) && !/boundary/.test(l.tipo));
    for (const c of calles) {
      for (let i = 1; i < c.puntos.length; i++) {
        const [ax, ay] = c.puntos[i - 1], [bx, by] = c.puntos[i];
        const t = { ax, ay, bx, by, nombre: c.nombre, tipo: c.tipo };
        // los tramos miden ≤ 6 m (densificados), basta con registrar ambos extremos
        for (const k of new Set([this.clave(ax, ay), this.clave(bx, by)])) {
          const lista = this.celdas.get(k);
          if (lista) lista.push(t);
          else this.celdas.set(k, [t]);
        }
      }
    }
  }

  private clave(x: number, y: number) {
    return `${Math.floor(x / CELDA)},${Math.floor(y / CELDA)}`;
  }

  /** Calle con nombre más cercana (hasta ~60 m). Prefiere calles con nombre sobre senderos sin nombre. */
  calle(x: number, y: number): { nombre: string; distancia: number } | null {
    const cx = Math.floor(x / CELDA), cy = Math.floor(y / CELDA);
    let mejor: { nombre: string; distancia: number } | null = null;
    for (let i = -1; i <= 1; i++)
      for (let j = -1; j <= 1; j++)
        for (const t of this.celdas.get(`${cx + i},${cy + j}`) ?? []) {
          if (!t.nombre) continue;
          const d = distTramo(x, y, t);
          if (!mejor || d < mejor.distancia) mejor = { nombre: t.nombre, distancia: d };
        }
    return mejor;
  }

  cercanos(x: number, y: number, radio = 80, max = 4): { nombre: string; distancia: number }[] {
    return this.lugares
      .map((l) => ({ nombre: l.nombre, distancia: Math.hypot(l.x - x, l.y - y) }))
      .filter((l) => l.distancia <= radio)
      .sort((a, b) => a.distancia - b.distancia)
      .filter((l, i, arr) => arr.findIndex((o) => o.nombre === l.nombre) === i)
      .slice(0, max);
  }
}
