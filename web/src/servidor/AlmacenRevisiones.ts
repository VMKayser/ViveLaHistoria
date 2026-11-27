// Solo servidor (rutas /api). Guarda y lee las revisiones en coordinacion/revisiones/<id>/ y ubica cada una en el
// reparto (manzana, edificio y agente dueño) para que el agente que corresponde la encuentre.
import { promises as fs } from "fs";
import path from "path";
import { aLatLon } from "@/mapa/geo";
import type { Lugar, NuevaRevision, Punto3, Revision } from "@/ciudad/revision/tipos";

const RAIZ = path.resolve(process.cwd(), "..");
export const CARPETA_REVISIONES = path.join(RAIZ, "coordinacion", "revisiones");
const REPARTO = path.join(RAIZ, "reparto", "manzanas.json");

type Poligono = [number, number][];
type Reparto = {
  manzanas: { id: string; dueno: string; centro: [number, number]; edificios: { id: string; huella: Poligono; centro: [number, number] }[] }[];
  espacios: { id: string; dueno: string; poligono?: Poligono }[];
  zona: { xmin: number; ymin: number; xmax: number; ymax: number };
};

function dentro(x: number, y: number, pts: Poligono) {
  let r = false;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [xi, yi] = pts[i], [xj, yj] = pts[j];
    if (yi > y !== yj > y && x < xi + ((y - yi) * (xj - xi)) / (yj - yi)) r = !r;
  }
  return r;
}

/** Dado un punto del lienzo, qué manzana, edificio o espacio es y de quién. */
export class LocalizadorReparto {
  private reparto: Reparto | null = null;

  private async datos(): Promise<Reparto> {
    this.reparto ??= JSON.parse(await fs.readFile(REPARTO, "utf8")) as Reparto;
    return this.reparto;
  }

  async ubicar(p: Punto3 | null): Promise<Lugar> {
    const vacio: Lugar = { manzana: null, edificio: null, espacio: null, asignado: null, lat: null, lon: null };
    if (!p) return vacio;
    const [lat, lon] = aLatLon(p.x, p.y);
    const r = await this.datos();
    const base = { ...vacio, lat: +lat.toFixed(7), lon: +lon.toFixed(7) };
    // 1) dentro de la huella de un edificio
    for (const m of r.manzanas) {
      for (const e of m.edificios) {
        if (dentro(p.x, p.y, e.huella)) return { ...base, manzana: m.id, edificio: e.id, asignado: m.dueno };
      }
    }
    // 2) dentro de un espacio con polígono (plaza)
    for (const s of r.espacios) {
      if (s.poligono && dentro(p.x, p.y, s.poligono)) return { ...base, espacio: s.id, asignado: s.dueno };
    }
    // 3) cerca de una fachada (hasta 6 m: lo enmarcado suele ser el frente, que el lienzo corre hacia adentro)
    let mejor: { d: number; m: string; e: string; dueno: string } | null = null;
    for (const m of r.manzanas) {
      for (const e of m.edificios) {
        const d = distanciaPoligono(p.x, p.y, e.huella);
        if (d < 6 && (!mejor || d < mejor.d)) mejor = { d, m: m.id, e: e.id, dueno: m.dueno };
      }
    }
    if (mejor) return { ...base, manzana: mejor.m, edificio: mejor.e, asignado: mejor.dueno };
    // 4) dentro de la zona: calle o vereda → BASE
    const z = r.zona;
    if (p.x >= z.xmin && p.x <= z.xmax && p.y >= z.ymin && p.y <= z.ymax) {
      const b = r.espacios.find((s) => s.id === "BASE");
      return { ...base, espacio: "BASE", asignado: b?.dueno ?? null };
    }
    return base;
  }
}

function distanciaPoligono(x: number, y: number, pts: Poligono) {
  let mejor = Infinity;
  for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) {
    const [ax, ay] = pts[j], [bx, by] = pts[i];
    const dx = bx - ax, dy = by - ay;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy || 1)));
    mejor = Math.min(mejor, Math.hypot(x - (ax + t * dx), y - (ay + t * dy)));
  }
  return mejor;
}

export type ArchivosEntrantes = { captura: Buffer; recorte: Buffer; referencia: Buffer | null };

export class AlmacenRevisiones {
  constructor(private readonly localizador = new LocalizadorReparto()) {}

  async listar(): Promise<Revision[]> {
    let ids: string[] = [];
    try {
      ids = (await fs.readdir(CARPETA_REVISIONES, { withFileTypes: true })).filter((d) => d.isDirectory()).map((d) => d.name);
    } catch {
      return [];
    }
    const lista = await Promise.all(ids.map(async (id) => {
      try {
        return JSON.parse(await fs.readFile(path.join(CARPETA_REVISIONES, id, "revision.json"), "utf8")) as Revision;
      } catch {
        return null;
      }
    }));
    return lista.filter((r): r is Revision => !!r).sort((a, b) => a.id.localeCompare(b.id));
  }

  async crear(datos: NuevaRevision, archivos: ArchivosEntrantes): Promise<Revision> {
    await fs.mkdir(CARPETA_REVISIONES, { recursive: true });
    const id = await this.reservarId();
    const dir = path.join(CARPETA_REVISIONES, id);
    const rev: Revision = {
      id,
      creada: new Date().toISOString(),
      autor: datos.autor.trim() || "usuario",
      estado: "pendiente",
      categoria: datos.categoria,
      prioridad: datos.prioridad,
      comentario: datos.comentario.trim(),
      lugar: await this.localizador.ubicar(datos.escena.centro),
      escena: datos.escena,
      archivos: {
        captura: "captura.jpg",
        recorte: "recorte.jpg",
        referencia: archivos.referencia ? "referencia.jpg" : null,
        fotos_proyecto: datos.fotos_proyecto,
      },
      resolucion: null,
    };
    await fs.writeFile(path.join(dir, "captura.jpg"), archivos.captura);
    await fs.writeFile(path.join(dir, "recorte.jpg"), archivos.recorte);
    if (archivos.referencia) await fs.writeFile(path.join(dir, "referencia.jpg"), archivos.referencia);
    const tmp = path.join(dir, "revision.json.tmp");
    await fs.writeFile(tmp, JSON.stringify(rev, null, 2) + "\n");
    await fs.rename(tmp, path.join(dir, "revision.json"));
    return rev;
  }

  async imagen(id: string, archivo: string): Promise<Buffer | null> {
    if (!/^R\d{4}$/.test(id) || !/^[a-z_]+\.jpg$/.test(archivo)) return null;
    try {
      return await fs.readFile(path.join(CARPETA_REVISIONES, id, archivo));
    } catch {
      return null;
    }
  }

  /** Crea la carpeta del siguiente número libre (mkdir sin recursive falla si ya existe: no hay carreras). */
  private async reservarId(): Promise<string> {
    const nombres = await fs.readdir(CARPETA_REVISIONES).catch(() => [] as string[]);
    const ultimo = Math.max(0, ...nombres.map((n) => Number(/^R(\d{4})$/.exec(n)?.[1] ?? 0)));
    for (let n = ultimo + 1; ; n++) {
      const id = `R${String(n).padStart(4, "0")}`;
      try {
        await fs.mkdir(path.join(CARPETA_REVISIONES, id));
        return id;
      } catch {
        // la tomó otra petición al mismo tiempo: probar la siguiente
      }
    }
  }
}
