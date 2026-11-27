"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import type { Lugar } from "@/components/CityScene";

const CityScene = dynamic(() => import("@/components/CityScene"), { ssr: false });

export default function PaginaPiloto() {
  const [lugar, setLugar] = useState<Lugar | null>(null);

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-sky-100">
      <CityScene seleccionado={lugar} onSelect={setLugar} />

      <header className="pointer-events-none absolute left-4 top-4 rounded-xl bg-white/85 px-4 py-2 shadow">
        <h1 className="text-lg font-bold text-stone-800">Mi Ciudad 3D · Piloto</h1>
        <p className="text-xs text-stone-600">Arrastra para moverte · rueda o pellizco para acercarte</p>
      </header>

      {lugar && (
        <aside className="absolute bottom-4 left-4 right-4 max-w-sm rounded-2xl bg-white/95 p-5 shadow-xl sm:left-auto">
          <button onClick={() => setLugar(null)} className="absolute right-3 top-2 text-xl text-stone-400 hover:text-stone-700" aria-label="Cerrar">
            ×
          </button>
          <p className="text-xs font-semibold uppercase tracking-wide text-amber-600">{lugar.anio}</p>
          <h2 className="mb-2 text-xl font-bold text-stone-800">{lugar.nombre}</h2>
          <p className="text-sm leading-relaxed text-stone-700">{lugar.descripcion}</p>
        </aside>
      )}
    </main>
  );
}
