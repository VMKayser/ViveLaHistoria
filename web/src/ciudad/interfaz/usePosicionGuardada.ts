// Recordar dónde estaba el usuario (pedido del usuario, 2026-11-12: "siempre que actualiza me mueve al inicio"):
// cada segundo se guarda en la sesión de la pestaña el modo, la posición, el rumbo y la inclinación; al recargar, si
// hay una posición guardada, se entra directo a ese punto sin pasar por la pantalla de inicio.
import { useEffect, useRef } from "react";
import type { EstadoVista } from "../motor/EstadoVista";
import type { Modo } from "../tipos";

const CLAVE = "sucre3d.posicion";
const VIGENCIA_MS = 12 * 3600 * 1000;

type Guardada = { modo: Modo; x: number; y: number; z: number; rumbo: number; inclinacion: number; t: number };

export function leerPosicion(): Guardada | null {
  try {
    const g = JSON.parse(sessionStorage.getItem(CLAVE) ?? "null") as Guardada | null;
    return g && Date.now() - g.t < VIGENCIA_MS && Number.isFinite(g.x) ? g : null;
  } catch {
    return null;
  }
}

/** Guarda la posición mientras se navega y, al tener la ciudad lista, vuelve a la última guardada (una vez). */
export function usePosicionGuardada(vista: EstadoVista, lista: boolean, entrado: boolean, entrar: (m: Modo) => void) {
  const restaurada = useRef(false);

  useEffect(() => {
    if (!entrado) return;
    const id = window.setInterval(() => {
      const g: Guardada = { modo: vista.modo, x: vista.x, y: vista.y, z: vista.z, rumbo: vista.rumbo, inclinacion: vista.inclinacion, t: Date.now() };
      try {
        sessionStorage.setItem(CLAVE, JSON.stringify(g));
      } catch {
        // sesión llena o bloqueada: no se recuerda la posición
      }
    }, 1000);
    return () => window.clearInterval(id);
  }, [vista, entrado]);

  useEffect(() => {
    if (!lista || restaurada.current) return;
    restaurada.current = true;
    const g = leerPosicion();
    if (!g) return;
    entrar(g.modo);
    // la escena del modo se monta en el cuadro siguiente: se espera un poco antes de mover la cámara
    const id = window.setTimeout(() => {
      if (g.modo === "peaton") vista.ordenar({ tipo: "toma", x: g.x, y: g.y, z: g.z, rumbo: g.rumbo, inclinacion: g.inclinacion });
      else vista.ordenar({ tipo: "ir", x: g.x, z: g.z });
    }, 700);
    return () => window.clearTimeout(id);
  }, [vista, lista, entrar]);
}
