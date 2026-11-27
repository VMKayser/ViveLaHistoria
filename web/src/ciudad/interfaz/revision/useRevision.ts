// Estado del modo revisión: activo o no, fase (navegar → enmarcar → formulario), lista de correcciones y la
// elegida. Encapsula la captura (EstadoVista.captura) y la conversión de una toma guardada a una orden de cámara.
import { useCallback, useEffect, useMemo, useState } from "react";
import type { EstadoVista } from "../../motor/EstadoVista";
import { ClienteRevisiones } from "../../revision/ClienteRevisiones";
import { Imagenes } from "../../revision/Imagenes";
import type { Revision } from "../../revision/tipos";
import type { Encuadre } from "./FormularioRevision";
import type { Marco } from "./Enmarcador";

export type Fase = { tipo: "navegar" } | { tipo: "enmarcar" } | { tipo: "formulario"; encuadre: Encuadre };

export function useRevision(vista: EstadoVista) {
  const cliente = useMemo(() => new ClienteRevisiones(), []);
  const [activo, setActivo] = useState(false);
  const [fase, setFase] = useState<Fase>({ tipo: "navegar" });
  const [revisiones, setRevisiones] = useState<Revision[]>([]);
  const [elegida, setElegida] = useState<string | null>(null);
  const [lista, setLista] = useState(false);
  const [aviso, setAviso] = useState("");

  const recargar = useCallback(() => {
    cliente.listar().then(setRevisiones).catch(() => setAviso("No se pudieron leer las correcciones (¿servidor local?)"));
  }, [cliente]);
  useEffect(() => {
    if (activo) recargar();
  }, [activo, recargar]);
  useEffect(() => {
    if (!aviso) return;
    const t = window.setTimeout(() => setAviso(""), 4000);
    return () => window.clearTimeout(t);
  }, [aviso]);

  const marcar = useCallback(async (m: Marco) => {
    const servicio = vista.captura;
    if (!servicio) return setFase({ tipo: "navegar" });
    const { lienzo, datos } = await servicio.capturar(m);
    const img = await Imagenes.componer(lienzo, datos.marco);
    setFase({ tipo: "formulario", encuadre: { datos, ...img } });
  }, [vista]);

  const guardada = useCallback((r: Revision) => {
    setRevisiones((l) => [...l, r]);
    setFase({ tipo: "navegar" });
    setAviso(`Corrección ${r.id} guardada${r.lugar.asignado ? ` · para ${r.lugar.asignado}` : ""}`);
  }, []);

  /** Lleva la cámara a donde estaba al enmarcar (lienzo → web; grados → radianes). */
  const irA = useCallback((r: Revision) => {
    const c = r.escena.camara;
    vista.ordenar({ tipo: "toma", x: c.lienzo.x, y: c.lienzo.z, z: -c.lienzo.y,
      rumbo: (c.rumbo_grados * Math.PI) / 180, inclinacion: (c.inclinacion_grados * Math.PI) / 180 });
  }, [vista]);

  return {
    cliente, activo, fase, revisiones, elegida, lista, aviso,
    alternar: () => setActivo((v) => !v),
    enmarcar: () => { setActivo(true); setFase({ tipo: "enmarcar" }); },
    cancelar: () => setFase({ tipo: "navegar" }),
    marcar, guardada, irA,
    elegir: (id: string | null) => { setElegida(id); if (id) setLista(true); },
    setLista,
  };
}
