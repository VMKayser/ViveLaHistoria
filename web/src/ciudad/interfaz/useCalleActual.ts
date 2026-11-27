// Nombre de la calle donde está el observador (a pie) o la que mira la cámara (vista aérea). Se consulta unas
// pocas veces por segundo; React solo se entera cuando el nombre cambia.
import { useEffect, useState } from "react";
import type { Buscador } from "@/mapa/busqueda";
import type { EstadoVista } from "../motor/EstadoVista";

export function useCalleActual(vista: EstadoVista, buscador: Buscador | null, distanciaMax = 14): string {
  const [calle, setCalle] = useState("");
  useEffect(() => {
    if (!buscador) return;
    const t = window.setInterval(() => {
      const c = buscador.calle(vista.x, -vista.z);
      const nombre = c && c.distancia <= distanciaMax ? c.nombre : "";
      setCalle((antes) => (antes === nombre ? antes : nombre));
    }, 300);
    return () => window.clearInterval(t);
  }, [vista, buscador, distanciaMax]);
  return calle;
}
