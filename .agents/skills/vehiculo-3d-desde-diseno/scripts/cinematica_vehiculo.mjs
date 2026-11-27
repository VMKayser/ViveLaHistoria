/* Cinemática reutilizable de vehículo en metros, segundos y radianes.
 * Coordenadas GLB/Three.js: +X delante, +Y arriba, +Z derecha.
 * Referencia sobre centro del eje trasero, dirección Ackermann y rodadura firmada por rueda.
 */
const TAU = Math.PI * 2;
const limitar = (x, a, b) => Math.max(a, Math.min(b, x));
const acercar = (actual, destino, maximo) => actual + limitar(destino - actual, -maximo, maximo);
const finito = (x, nombre) => {
  if (!Number.isFinite(x)) throw new TypeError(`${nombre} debe ser finito`);
  return x;
};

export const NOMBRES_RUEDAS = [
  'rueda_trasera_derecha',
  'rueda_trasera_izquierda',
  'rueda_delantera_derecha',
  'rueda_delantera_izquierda',
];

export const envolverAngulo = angulo => ((angulo % TAU) + TAU) % TAU;

export function configurarMovimiento(datos) {
  return {
    ...datos.movimiento,
    radio_rueda: datos.radio_rueda,
    eje_trasero: datos.ejes[0],
    eje_delantero: datos.ejes[1],
    semivia: datos.semivia_ruedas,
  };
}

export class CinematicaVehiculo {
  constructor(configuracion) {
    this.config = { ...configuracion };
    const c = this.config;
    for (const clave of [
      'radio_rueda',
      'semivia',
      'velocidad_maxima',
      'retroceso_maximo',
      'aceleracion',
      'frenada',
      'direccion_maxima',
      'rapidez_direccion',
    ]) {
      if (!(finito(c[clave], clave) > 0)) throw new RangeError(`${clave} debe ser positivo`);
    }
    this.batalla = finito(c.eje_delantero, 'eje_delantero') - finito(c.eje_trasero, 'eje_trasero');
    if (
      this.batalla <= 0 ||
      c.direccion_maxima >= Math.PI / 2 ||
      Math.tan(c.direccion_maxima) * c.semivia >= this.batalla
    ) {
      throw new RangeError('Geometría de dirección inválida');
    }
    this.distancias = Object.fromEntries(NOMBRES_RUEDAS.map(n => [n, 0]));
    this.velocidadObjetivo = 0;
    this.direccionObjetivo = 0;
    this.teletransportar({ x: 0, z: 0, rumbo: 0 }, true);
  }

  entrada({ velocidad = this.velocidadObjetivo, direccion = this.direccionObjetivo } = {}) {
    this.velocidadObjetivo = limitar(
      finito(velocidad, 'velocidad'),
      -this.config.retroceso_maximo,
      this.config.velocidad_maxima
    );
    this.direccionObjetivo = limitar(
      finito(direccion, 'direccion'),
      -this.config.direccion_maxima,
      this.config.direccion_maxima
    );
  }

  teletransportar({ x, z, rumbo }, reiniciarRuedas = false) {
    this.x = finito(x, 'x');
    this.z = finito(z, 'z');
    this.rumbo = finito(rumbo, 'rumbo');
    this.traseroX = x + this.config.eje_trasero * Math.cos(rumbo);
    this.traseroZ = z - this.config.eje_trasero * Math.sin(rumbo);
    this.velocidad = 0;
    this.velocidadObjetivo = 0;
    this.direccion = 0;
    this.direccionObjetivo = 0;
    if (reiniciarRuedas) {
      for (const n of NOMBRES_RUEDAS) this.distancias[n] = 0;
    }
  }

  avanzarDistancia(distancia, curvatura = Math.tan(this.direccion) / this.batalla) {
    finito(distancia, 'distancia');
    finito(curvatura, 'curvatura');
    if (Math.abs(curvatura) > Math.tan(this.config.direccion_maxima) / this.batalla + 1e-9) {
      throw new RangeError('La curva supera el ángulo máximo de dirección del vehículo');
    }
    const giro = distancia * curvatura;
    const medio = this.rumbo + giro / 2;
    const arco = Math.abs(giro) < 1e-8 ? distancia : (distancia * Math.sin(giro / 2)) / (giro / 2);
    this.traseroX += arco * Math.cos(medio);
    this.traseroZ -= arco * Math.sin(medio);
    this.rumbo += giro;
    this.x = this.traseroX - this.config.eje_trasero * Math.cos(this.rumbo);
    this.z = this.traseroZ + this.config.eje_trasero * Math.sin(this.rumbo);
    for (const nombre of NOMBRES_RUEDAS) {
      const lateral = nombre.endsWith('_derecha') ? this.config.semivia : -this.config.semivia;
      const longitudinal = nombre.includes('_delantera_') ? this.batalla : 0;
      this.distancias[nombre] += distancia * Math.hypot(1 + curvatura * lateral, curvatura * longitudinal);
    }
    this.direccion = Math.atan(curvatura * this.batalla);
  }

  actualizar(dt) {
    if (finito(dt, 'dt') < 0) throw new RangeError('dt no puede ser negativo');
    if (dt === 0) return this.estado();
    const pasos = Math.ceil(dt * 120);
    const h = dt / pasos;
    for (let i = 0; i < pasos; i++) {
      const anterior = this.velocidad;
      const invirtiendo = anterior * this.velocidadObjetivo < 0;
      const frenando = invirtiendo || Math.abs(this.velocidadObjetivo) < Math.abs(anterior);
      const destino = invirtiendo ? 0 : this.velocidadObjetivo;
      this.velocidad = acercar(
        anterior,
        destino,
        h * (frenando ? this.config.frenada : this.config.aceleracion)
      );
      const dirAnterior = this.direccion;
      const dirNueva = acercar(dirAnterior, this.direccionObjetivo, h * this.config.rapidez_direccion);
      this.avanzarDistancia(
        ((anterior + this.velocidad) * h) / 2,
        Math.tan((dirAnterior + dirNueva) / 2) / this.batalla
      );
      this.direccion = dirNueva;
    }
    return this.estado();
  }

  estado() {
    const curvatura = Math.tan(this.direccion) / this.batalla;
    const ruedas = {};
    for (const nombre of NOMBRES_RUEDAS) {
      const lateral = nombre.endsWith('_derecha') ? this.config.semivia : -this.config.semivia;
      ruedas[nombre] = {
        distancia: this.distancias[nombre],
        rodadura: -this.distancias[nombre] / this.config.radio_rueda,
        direccion: nombre.includes('_delantera_')
          ? Math.atan2(curvatura * this.batalla, 1 + curvatura * lateral)
          : 0,
      };
    }
    return {
      x: this.x,
      z: this.z,
      rumbo: this.rumbo,
      velocidad: this.velocidad,
      direccion: this.direccion,
      ruedas,
    };
  }
}

function encontrarRaizVehiculo(modelo, nombreRaiz) {
  if (nombreRaiz) return modelo.getObjectByName(nombreRaiz);
  let hallado = null;
  modelo.traverse(o => {
    if (!hallado && o.userData && o.userData.movimiento) hallado = o;
  });
  return hallado;
}

export class VehiculoAnimado {
  constructor(modelo, configuracion = null, nombreRaiz = null) {
    this.raiz = encontrarRaizVehiculo(modelo, nombreRaiz);
    if (!this.raiz) throw new Error(`Falta el nodo raíz del vehículo (${nombreRaiz || 'userData.movimiento'})`);
    this.cinematica = new CinematicaVehiculo(configuracion || this.raiz.userData.movimiento);
    this.ruedas = NOMBRES_RUEDAS.map(nombre => {
      const rueda = modelo.getObjectByName(nombre);
      if (!rueda) throw new Error(`Falta el pivote ${nombre}`);
      const direccion = nombre.includes('_delantera_')
        ? modelo.getObjectByName(nombre.replace('rueda_', 'direccion_'))
        : null;
      if (nombre.includes('_delantera_') && (!direccion || rueda.parent !== direccion)) {
        throw new Error(`Falta el pivote padre de dirección para ${nombre}`);
      }
      return { nombre, rueda, direccion, reposo: rueda.quaternion.clone() };
    });
    this.teletransportar(
      { x: this.raiz.position.x, z: this.raiz.position.z, rumbo: this.raiz.rotation.y },
      true
    );
  }

  entrada(orden) {
    this.cinematica.entrada(orden);
  }

  actualizar(dt) {
    const estado = this.cinematica.actualizar(dt);
    this.aplicar(estado);
    return estado;
  }

  avanzarDistancia(distancia, curvatura = 0) {
    this.cinematica.avanzarDistancia(distancia, curvatura);
    const estado = this.cinematica.estado();
    this.aplicar(estado);
    return estado;
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

  estado() {
    return this.cinematica.estado();
  }
}
