"use client";

// Panel del taller (herramienta interna, no del producto): avance de los agentes, ir a una manzana, volúmenes del
// lienzo y medición de rendimiento. Se abre con la tecla T o con ?taller en la dirección.
import { useEffect, useState } from "react";
import type { NivelCalidad } from "../motor/calidad";
import type { EstadoVista } from "../motor/EstadoVista";
import { AGENTES, type Modelo } from "../tipos";

const COLOR_AGENTE: Record<string, string> = { claude: "bg-orange-600", codex: "bg-sky-700" };

export default function PanelTaller({ vista, modelos, centros, visibles, setVisibles, volumenes, setVolumenes, nivel, alCerrar }: {
  vista: EstadoVista;
  modelos: Modelo[];
  centros: Map<string, { x: number; z: number }>;
  visibles: Record<string, boolean>;
  setVisibles: (v: Record<string, boolean>) => void;
  volumenes: boolean;
  setVolumenes: (v: boolean) => void;
  nivel: NivelCalidad;
  alCerrar: () => void;
}) {
  const [r, setR] = useState(vista.rendimiento);
  useEffect(() => {
    const t = window.setInterval(() => setR({ ...vista.rendimiento }), 1000);
    return () => window.clearInterval(t);
  }, [vista]);
  const total = modelos.reduce((t, m) => t + m.triangulos, 0);

  return (
    <aside className="panel pointer-events-auto max-h-[calc(100dvh-330px)] w-72 overflow-y-auto p-3 text-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-bold">Taller · avance del modelado</h2>
        <button onClick={alCerrar} className="rounded px-1.5 text-sucre-tinta-suave hover:bg-sucre-oro-claro" title="Cerrar (T)">✕</button>
      </div>
      <p className="my-1.5 font-mono text-[11px] text-sucre-tinta-suave">
        {r.fps} fps · {r.llamadas} llamadas · {(r.triangulos / 1e6).toFixed(2)} M tri/cuadro · calidad {nivel}
      </p>
      <p className="mb-2 text-xs text-sucre-tinta-suave">
        {modelos.length} modelos · {(total / 1000).toFixed(0)} mil triángulos
      </p>
      {AGENTES.map((a) => {
        const suyos = modelos.filter((m) => m.agente === a);
        return (
          <div key={a} className="mb-2">
            <label className="flex items-center gap-2 font-semibold">
              <input type="checkbox" checked={visibles[a] !== false}
                onChange={(e) => setVisibles({ ...visibles, [a]: e.target.checked })} />
              <span className={`inline-block h-3 w-3 rounded-full ${COLOR_AGENTE[a]}`} />
              {a} ({suyos.length})
            </label>
            <div className="flex flex-wrap gap-1 pl-6 pt-1">
              {suyos.length === 0 && <span className="text-xs text-sucre-tinta-suave">todavía nada</span>}
              {suyos.map((m) => {
                const c = centros.get(`${m.agente}/${m.id}`);
                return (
                  <button key={m.id} disabled={!c} onClick={() => c && vista.ordenar({ tipo: "ir", x: c.x, z: c.z })}
                    title={`${(m.triangulos / 1000).toFixed(0)} mil triángulos · ${m.actualizado}`}
                    className="rounded border border-sucre-tinta/15 px-1.5 py-0.5 text-xs hover:bg-sucre-oro-claro disabled:opacity-40">
                    {m.id}
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}
      <label className="flex items-start gap-2 border-t border-sucre-tinta/10 pt-2 text-xs">
        <input type="checkbox" checked={volumenes} onChange={(e) => setVolumenes(e.target.checked)} className="mt-0.5" />
        Volúmenes del lienzo (lo que falta modelar; se ocultan donde ya hay manzanas)
      </label>
      <p className="mt-2 text-[11px] text-sucre-tinta-suave">Lo último exportado aparece después de <code>npm run ciudad</code> y recargar.</p>
    </aside>
  );
}
