// una sesion de un usuario de qolqe, igual en todas las pruebas:
// inicia sesion y hace 6 operaciones con una pausa de 10 a 25 s entre una y otra.
// cada operacion sale al azar con los porcentajes del requerimiento.
import http from 'k6/http';
import { check, sleep } from 'k6';
import exec from 'k6/execution';
import { SharedArray } from 'k6/data';
import { Counter } from 'k6/metrics';

const URL = __ENV.QOLQE_URL || 'http://localhost:8000';

// datos/usuarios.csv lo genera datos/preparar_datos.py
const usuarios = new SharedArray('usuarios', () =>
  open('./datos/usuarios.csv').trim().split('\n').slice(1).map((linea) => {
    const [celular, pin, suministros] = linea.split(',');
    return { celular, pin, suministros: suministros.split(';') };
  }),
);

// tabla del requerimiento; deudas y pagos se separan en 6 % y 4 %
const OPERACIONES = [
  ['saldo_perfil', 30],
  ['movimientos', 15],
  ['transferencia', 15],
  ['contactos', 10],
  ['recarga', 10],
  ['deudas', 6],
  ['pago', 4],
  ['otras', 10],
];
const OTRAS = ['/api/limites', '/api/limites/alertas', '/api/solicitudes',
  '/api/seguridad/dispositivos', '/api/seguridad/sesiones'];

const sesiones = new Counter('sesiones');
const erroresNegocio = new Counter('errores_negocio'); // 4xx: problema de datos, no de rendimiento
const dineroOk = new Counter('dinero_ok'); // 201 de transferencias, recargas y pagos

// por vu: que suministro toca pagar (cada suministro tiene una sola deuda)
let siguienteSuministro = 0;

export function sesion() {
  const yo = exec.vu.idInTest - 1;
  if (yo >= usuarios.length) {
    exec.test.abort(`hay ${usuarios.length} usuarios y se necesitan mas: corre preparar_datos.py con un numero mayor`);
  }
  const usuario = usuarios[yo];

  const login = pedir('POST', '/api/auth/login', 'login', 'consulta', null,
    { celular: usuario.celular, pin: usuario.pin });
  if (login.status !== 200) {
    sleep(pausa());
    return;
  }
  const token = login.json('access_token');

  for (let i = 0; i < 6; i++) {
    sleep(pausa());
    operar(elegir(), usuario, token);
  }
  sesiones.add(1);
}

function operar(operacion, usuario, token) {
  if (operacion === 'saldo_perfil') {
    const ruta = Math.random() < 0.5 ? '/api/cuentas/me/saldo' : '/api/cuentas/me';
    pedir('GET', ruta, operacion, 'consulta', token);
  } else if (operacion === 'movimientos') {
    pedir('GET', '/api/movimientos', operacion, 'consulta', token);
  } else if (operacion === 'transferencia') {
    pedir('POST', '/api/transferencias', operacion, 'dinero', token,
      { celular_destino: otroUsuario().celular, monto: entero(1, 20) });
  } else if (operacion === 'contactos') {
    const ruta = Math.random() < 0.5 ? '/api/contactos' : '/api/contactos?buscar=carga';
    pedir('GET', ruta, operacion, 'consulta', token);
  } else if (operacion === 'recarga') {
    // un numero al azar: el maximo es de 5 recargas al dia al mismo numero
    pedir('POST', '/api/recargas', operacion, 'dinero', token,
      { celular: `9${entero(10000000, 99999999)}`, monto: [5, 10, 20, 30][entero(0, 3)] });
  } else if (operacion === 'deudas') {
    consultarDeuda(usuario, token);
  } else if (operacion === 'pago') {
    const deuda = consultarDeuda(usuario, token);
    if (deuda.status === 200) {
      pedir('POST', '/api/servicios/pagos', operacion, 'dinero', token, { deuda_id: deuda.json('0.id') });
      siguienteSuministro++;
    }
  } else {
    pedir('GET', OTRAS[entero(0, OTRAS.length - 1)], operacion, 'consulta', token);
  }
}

function consultarDeuda(usuario, token) {
  const suministro = usuario.suministros[siguienteSuministro % usuario.suministros.length];
  return pedir('GET', `/api/servicios/deudas?empresa=AGUA&suministro=${suministro}`, 'deudas', 'consulta', token);
}

function pedir(metodo, ruta, operacion, tipo, token, cuerpo) {
  const cabeceras = { 'Content-Type': 'application/json' };
  if (token) cabeceras.Authorization = `Bearer ${token}`;
  const etiquetas = { op: operacion, tipo, name: ruta.split('?')[0] };
  const r = http.request(metodo, URL + ruta, cuerpo ? JSON.stringify(cuerpo) : null,
    { headers: cabeceras, tags: etiquetas });

  check(r, { 'responde 2xx': (x) => x.status >= 200 && x.status < 300 }, etiquetas);
  if (r.status >= 400 && r.status < 500) {
    erroresNegocio.add(1, { op: operacion, codigo: codigoDeError(r) });
  }
  if (tipo === 'dinero' && r.status === 201) dineroOk.add(1, { op: operacion });
  return r;
}

function codigoDeError(r) {
  try {
    return r.json('codigo') || String(r.status);
  } catch (e) {
    return String(r.status);
  }
}

function elegir() {
  let azar = Math.random() * 100;
  for (const [operacion, peso] of OPERACIONES) {
    azar -= peso;
    if (azar < 0) return operacion;
  }
  return 'otras';
}

// cualquier otro usuario de la lista, nunca uno mismo
function otroUsuario() {
  let otro = entero(0, usuarios.length - 1);
  if (otro === exec.vu.idInTest - 1) otro = (otro + 1) % usuarios.length;
  return usuarios[otro];
}

function entero(min, max) {
  return min + Math.floor(Math.random() * (max - min + 1));
}

// de 10 a 25 s con promedio 18 s: distribucion triangular con moda 19, (10 + 19 + 25) / 3 = 18
function pausa() {
  const [a, moda, b] = [10, 19, 25];
  const u = Math.random();
  if (u < (moda - a) / (b - a)) return a + Math.sqrt(u * (b - a) * (moda - a));
  return b - Math.sqrt((1 - u) * (b - a) * (b - moda));
}
