import { CinematicaVehiculo, NOMBRES_RUEDAS, envolverAngulo } from '../cinematica_vehiculo.mjs';

const delanteras = NOMBRES_RUEDAS.filter(nombre => nombre.includes('_delantera_'));
const reposoRuedas = new WeakMap();

export class CinematicaCarruaje extends CinematicaVehiculo {
  constructor(config) {
    super(config);
    this.radioDelantero = config.radios_ruedas.delantera;
    this.radioTrasero = config.radios_ruedas.trasera;
    this.lanza = config.enganche.distancia_al_eje_delantero_m;
    if (![this.radioDelantero, this.radioTrasero, this.lanza].every(v => Number.isFinite(v) && v > 0)) {
      throw new RangeError('Los radios y la distancia de tiro deben ser positivos');
    }
  }

  teletransportar(pose, reiniciarRuedas = false) {
    super.teletransportar(pose, reiniciarRuedas);
    if (reiniciarRuedas) this.distanciaCaballo = 0;
  }

  vectorCaballo(curvatura) {
    const delta = Math.atan(curvatura * this.batalla);
    return [
      1 - curvatura * this.lanza * Math.sin(delta),
      curvatura * (this.batalla + this.lanza * Math.cos(delta)),
    ];
  }

  avanzarDistancia(ds, k = Math.tan(this.direccion) / this.batalla) {
    const distancias = delanteras.map(n => this.distancias[n]);
    super.avanzarDistancia(ds, k);
    // El eje delantero completo gira en su corona. En curva, cada cubo
    // recorre un arco concéntrico a una distancia distinta de la corona.
    const centro = Math.hypot(1, this.batalla * k);
    delanteras.forEach((nombre, i) => {
      const lado = nombre.endsWith('_derecha') ? 1 : -1;
      this.distancias[nombre] = distancias[i] + ds * (centro + k * lado * this.config.semivia);
    });
    this.distanciaCaballo += ds * Math.hypot(...this.vectorCaballo(k));
  }

  estado() {
    const estado = super.estado();
    const k = Math.tan(estado.direccion) / this.batalla;
    for (const nombre of NOMBRES_RUEDAS) {
      const del = delanteras.includes(nombre);
      Object.assign(estado.ruedas[nombre], {
        rodadura: -this.distancias[nombre] / (del ? this.radioDelantero : this.radioTrasero),
        direccion: del ? estado.direccion : 0,
      });
    }
    const [vx, vz] = this.vectorCaballo(k);
    estado.rumboCaballoRelativo = Math.atan2(vz, vx) - estado.direccion;
    estado.distanciaCaballo = this.distanciaCaballo;
    return estado;
  }
}

export class CarruajeAnimado {
  constructor(escena, nombre) {
    this.raiz = escena.getObjectByName(nombre);
    this.tornamesa = escena.getObjectByName('tornamesa_delantera');
    if (!this.raiz || !this.tornamesa) throw new Error('Falta la raíz o la tornamesa del carruaje');
    this.cinematica = new CinematicaCarruaje(this.raiz.userData.movimiento);
    this.ruedas = NOMBRES_RUEDAS.map(n => {
      const rueda = escena.getObjectByName(n);
      if (!rueda) throw new Error(`Falta la rueda ${n}`);
      if (!reposoRuedas.has(rueda)) reposoRuedas.set(rueda, rueda.quaternion.clone());
      return { nombre: n, rueda, reposo: reposoRuedas.get(rueda) };
    });
    this.actualizar(0);
  }

  actualizar(dt, orden) {
    if (orden) this.cinematica.entrada(orden);
    const estado = this.cinematica.actualizar(dt);
    this.raiz.position.x = estado.x;
    this.raiz.position.z = estado.z;
    this.raiz.rotation.y = estado.rumbo;
    this.tornamesa.rotation.y = estado.direccion;
    for (const { nombre, rueda, reposo } of this.ruedas) {
      rueda.quaternion.copy(reposo);
      rueda.rotateZ(envolverAngulo(estado.ruedas[nombre].rodadura));
    }
    return estado;
  }
}
