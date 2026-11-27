import { CinematicaVehiculo, NOMBRES_RUEDAS, envolverAngulo } from './cinematica_vehiculo.mjs';

// Adaptador Three.js sin dependencias adicionales. Conserva los materiales y la
// jerarquía del GLB; se puede trasladar al visor urbano sin copiar el controlador.
export class AutobusAnimado {
  constructor(modelo, configuracion, nombreRaiz = 'autobus_bronco') {
    this.raiz = modelo.getObjectByName(nombreRaiz);
    if (!this.raiz) throw new Error(`Falta la raíz ${nombreRaiz}`);
    this.cinematica = new CinematicaVehiculo(configuracion || this.raiz.userData.movimiento);
    this.ruedas = NOMBRES_RUEDAS.map(nombre => {
      const rueda = modelo.getObjectByName(nombre);
      if (!rueda) throw new Error(`Falta ${nombre}`);
      const direccion = nombre.includes('_delantera_')
        ? modelo.getObjectByName(nombre.replace('rueda_', 'direccion_')) : null;
      if (nombre.includes('_delantera_') && (!direccion || rueda.parent !== direccion))
        throw new Error(`Falta el pivote de dirección de ${nombre}`);
      return { nombre, rueda, direccion, reposo: rueda.quaternion.clone() };
    });
    this.teletransportar({ x: this.raiz.position.x, z: this.raiz.position.z, rumbo: this.raiz.rotation.y }, true);
  }

  entrada(orden) { this.cinematica.entrada(orden); }

  actualizar(dt) { const estado = this.cinematica.actualizar(dt); this.aplicar(estado); return estado; }

  avanzarDistancia(distancia, curvatura = 0) {
    this.cinematica.avanzarDistancia(distancia, curvatura);
    const estado = this.cinematica.estado(); this.aplicar(estado); return estado;
  }

  teletransportar(pose, reiniciarRuedas = false) {
    this.cinematica.teletransportar(pose, reiniciarRuedas);
    if (pose.y !== undefined) this.raiz.position.y = pose.y;
    this.aplicar(this.cinematica.estado());
  }

  aplicar(estado) {
    this.raiz.position.x = estado.x;
    this.raiz.position.z = estado.z;
    this.raiz.rotation.y = estado.rumbo;
    for (const { nombre, rueda, direccion, reposo } of this.ruedas) {
      if (direccion) direccion.rotation.y = estado.ruedas[nombre].direccion;
      rueda.quaternion.copy(reposo);
      rueda.rotateZ(envolverAngulo(estado.ruedas[nombre].rodadura));
    }
    this.raiz.updateMatrixWorld(true);
  }

  estado() { return this.cinematica.estado(); }
}

// El mismo contrato de ruedas sirve a los nuevos diseños, con su propia raíz.
export class VehiculoAnimado extends AutobusAnimado {
  constructor(modelo, nombreRaiz, configuracion) { super(modelo, configuracion, nombreRaiz); }
}
