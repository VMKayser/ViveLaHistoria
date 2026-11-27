// Lee los manifiestos que escriben los agentes al exportar y arma la lista de modelos a cargar.
import { AGENTES, type Modelo } from "../tipos";

type EntradaManifiesto = { archivo: string; triangulos: number; actualizado: string };
type EntradaOptimizada = { archivo: string; actualizado: string };

export class CatalogoModelos {
  constructor(private readonly raiz = "/models/ciudad") {}

  async cargar(): Promise<Modelo[]> {
    const optimizados = await this.optimizados();
    const listas = await Promise.all(AGENTES.map((a) => this.delAgente(a, optimizados)));
    return listas.flat();
  }

  /**
   * Copias comprimidas (npm run modelos:opt, ~5× más livianas): solo se usan si su marca 'actualizado' coincide con la
   * del manifiesto del agente, así nunca se carga un modelo viejo si el agente re-exportó después de comprimir.
   */
  private async optimizados(): Promise<Record<string, EntradaOptimizada>> {
    if (new URLSearchParams(window.location.search).has("crudo")) return {}; // diagnóstico: forzar los GLB originales
    try {
      const r = await fetch("/models/opt/manifiesto.json", { cache: "no-store" });
      return r.ok ? await r.json() : {};
    } catch {
      return {};
    }
  }

  private async delAgente(agente: string, optimizados: Record<string, EntradaOptimizada>): Promise<Modelo[]> {
    let man: Record<string, EntradaManifiesto> = {};
    try {
      const r = await fetch(`${this.raiz}/${agente}/manifiesto.json`, { cache: "no-store" });
      if (r.ok) man = await r.json();
    } catch {
      // sin manifiesto: el agente todavía no exportó nada
    }
    return Object.entries(man).map(([id, v]) => {
      const opt = optimizados[`${agente}/${id}`];
      const raiz = opt && opt.actualizado === v.actualizado ? `/models/opt` : this.raiz;
      return {
        agente,
        id,
        // el parámetro evita que el navegador use una versión vieja del GLB
        url: `${raiz}/${agente}/${v.archivo}?v=${encodeURIComponent(v.actualizado)}`,
        triangulos: v.triangulos,
        actualizado: v.actualizado,
      };
    });
  }
}
