import { VehiculoAnimado } from '../autobus_animado.mjs';
import { CarruajeAnimado } from '../carrozas/cinematica_carruaje.mjs';

/** El remolque gira el eje completo bajo la caja. */
class RemolqueAnimado extends CarruajeAnimado {
  entrada(orden) {
    this.cinematica.entrada(orden);
  }

  estado() {
    return this.cinematica.estado();
  }

  teletransportar(pose, reiniciarRuedas = false) {
    this.cinematica.teletransportar(pose,reiniciarRuedas);
    if (pose.y !== undefined) this.raiz.position.y=pose.y;
    return this.actualizar(0);
  }

  avanzarDistancia(distancia, curvatura = 0) {
    this.cinematica.avanzarDistancia(distancia,curvatura);
    return this.actualizar(0);
  }
}

export function crearConductor(modelo,id) {
  const datos=modelo.getObjectByName(id)?.userData.movimiento;
  return datos?.tipo_direccion==='tornamesa'
    ? new RemolqueAnimado(modelo,id)
    : new VehiculoAnimado(modelo,id);
}
