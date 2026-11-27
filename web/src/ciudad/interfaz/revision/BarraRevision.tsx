"use client";

// Botones del modo revisión (arriba a la derecha): activar/desactivar, enmarcar una zona y ver la lista.
export default function BarraRevision({ activo, pendientes, lista, alAlternar, alEnmarcar, alLista }: {
  activo: boolean;
  pendientes: number;
  lista: boolean;
  alAlternar: () => void;
  alEnmarcar: () => void;
  alLista: () => void;
}) {
  return (
    <div className="panel pointer-events-auto flex items-center gap-1 p-1 text-sm">
      <button onClick={alAlternar} title="Modo revisión (tecla V)"
        className={`rounded-lg px-3 py-1.5 font-semibold ${activo ? "bg-sucre-tinta text-white" : "hover:bg-sucre-oro-claro"}`}>
        Revisión
      </button>
      {activo && (
        <>
          <button onClick={alEnmarcar} title="Enmarcar una zona a corregir (tecla B)"
            className="flex items-center gap-1.5 rounded-lg bg-sucre-rojo px-3 py-1.5 font-semibold text-white hover:bg-sucre-rojo-oscuro">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" aria-hidden>
              <path d="M4 9V4h5M15 4h5v5M20 15v5h-5M9 20H4v-5" />
            </svg>
            Enmarcar
          </button>
          <button onClick={alLista} title="Correcciones guardadas"
            className={`rounded-lg px-3 py-1.5 font-semibold ${lista ? "bg-sucre-oro-claro" : "hover:bg-sucre-oro-claro"}`}>
            Lista{pendientes > 0 && <span className="ml-1.5 rounded-full bg-sucre-rojo px-1.5 text-[11px] text-white">{pendientes}</span>}
          </button>
        </>
      )}
    </div>
  );
}
