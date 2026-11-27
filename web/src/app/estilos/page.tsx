"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import { ESTILOS, estiloPorId, type EstiloId } from "@/estilos/estilos";

const EscenaEstilos = dynamic(() => import("@/estilos/EscenaEstilos"), { ssr: false });

export default function PaginaEstilos() {
  const [id, setId] = useState<EstiloId>("lowpoly");
  const [ui, setUi] = useState(true);

  // ?e=1..5 elige el estilo y ?ui=0 oculta la interfaz (para capturas)
  useEffect(() => {
    const q = new URLSearchParams(window.location.search);
    const n = Number(q.get("e"));
    if (n >= 1 && n <= ESTILOS.length) setId(ESTILOS[n - 1].id);
    if (q.get("ui") === "0") setUi(false);
  }, []);

  const estilo = estiloPorId(id);

  return (
    <main className="relative h-dvh w-full overflow-hidden" style={{ background: estilo.fondo }}>
      <EscenaEstilos estilo={estilo} />

      {ui && (
        <>
          <header className="pointer-events-none absolute left-4 top-4 max-w-md rounded-xl bg-white/90 px-4 py-3 shadow">
            <p className="text-xs font-semibold uppercase tracking-wide text-amber-700">Piloto de estilo · Catedral de Sucre y Plaza 25 de Mayo</p>
            <h1 className="text-lg font-bold text-stone-800">
              {estilo.numero}. {estilo.nombre}
            </h1>
            <p className="mt-1 text-sm text-stone-700">{estilo.resumen}</p>
            <p className="mt-2 text-xs text-stone-600">
              <b>Referencias:</b> {estilo.referencias}
            </p>
            <p className="mt-1 text-xs text-emerald-800">
              <b>A favor:</b> {estilo.pros}
            </p>
            <p className="mt-1 text-xs text-rose-800">
              <b>En contra:</b> {estilo.contras}
            </p>
          </header>

          <nav className="absolute bottom-4 left-1/2 flex max-w-[calc(100%-2rem)] -translate-x-1/2 gap-2 overflow-x-auto rounded-2xl bg-white/90 p-2 shadow-lg">
            {ESTILOS.map((e) => (
              <button
                key={e.id}
                onClick={() => setId(e.id)}
                className={`whitespace-nowrap rounded-xl px-3 py-2 text-sm font-semibold transition ${
                  e.id === id ? "bg-amber-500 text-white" : "text-stone-700 hover:bg-amber-100"
                }`}
              >
                {e.numero}. {e.nombre}
              </button>
            ))}
          </nav>
        </>
      )}
    </main>
  );
}
