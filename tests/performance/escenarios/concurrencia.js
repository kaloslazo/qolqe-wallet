// dinero bajo concurrencia: el mismo usuario manda varias operaciones a la vez
// (doble clic o reintentos de la app). ninguna puede saltarse el limite o el saldo
// ni aplicarse dos veces. cada ronda reinicia los datos, asi que se corre aparte:
//   k6 run escenarios/concurrencia.js
import http from 'k6/http';
import { check } from 'k6';
import { Counter } from 'k6/metrics';

const URL = __ENV.QOLQE_URL || 'http://localhost:8000';
const JSON_ = { 'Content-Type': 'application/json' };
const aceptadas = new Counter('aceptadas');

export const options = {
  scenarios: { rondas: { executor: 'per-vu-iterations', vus: 1, iterations: 5 } },
  thresholds: { checks: ['rate==1'] },
};

function entrar(celular, pin) {
  const r = http.post(`${URL}/api/auth/login`, JSON.stringify({ celular, pin }), { headers: JSON_ });
  return { headers: { ...JSON_, Authorization: `Bearer ${r.json('access_token')}` } };
}

// manda la misma peticion n veces en paralelo y cuenta cuantas respondieron 201
function aLaVez(n, ruta, cuerpo, sesion, caso) {
  const lote = Array.from({ length: n }, () => ['POST', URL + ruta, JSON.stringify(cuerpo), sesion]);
  const ok = http.batch(lote).filter((r) => r.status === 201).length;
  aceptadas.add(ok, { caso });
  return ok;
}

export default function () {
  http.del(`${URL}/api/pruebas/reloj`);
  http.post(`${URL}/api/pruebas/reiniciar`);

  // diego: limite diario S/ 1000 y saldo S/ 2500. cinco de S/ 300 a la vez: pasan 3 como maximo
  const diego = entrar('998877665', '3604');
  const t = aLaVez(5, '/api/transferencias', { celular_destino: '912345678', monto: 300 }, diego, 'limite');
  const usado = Number(http.get(`${URL}/api/limites`, diego).json('usado_hoy'));
  console.log(`diego: ${t} de 5 transferencias aceptadas, usado hoy S/ ${usado}`);
  check(usado, { 'diego no pasa su limite diario de S/ 1000': (u) => u <= 1000 });

  // carla: saldo S/ 50. dos de S/ 40 a la vez: solo una deberia pasar
  const carla = entrar('956781234', '5917');
  const c = aLaVez(2, '/api/transferencias', { celular_destino: '912345678', monto: 40 }, carla, 'saldo');
  const saldo = Number(http.get(`${URL}/api/cuentas/me/saldo`, carla).json('saldo'));
  console.log(`carla: ${c} de 2 transferencias aceptadas, saldo final S/ ${saldo}`);
  check(saldo, { 'el saldo de carla no queda negativo': (s) => s >= 0 });

  // usuario de carga 1: su deuda de agua pagada dos veces a la vez
  const u1 = entrar('900000001', '2580');
  const deuda = http.get(`${URL}/api/servicios/deudas?empresa=AGUA&suministro=4000000001`, u1).json('0.id');
  const p = aLaVez(2, '/api/servicios/pagos', { deuda_id: deuda }, u1, 'pago');
  console.log(`usuario 900000001: ${p} de 2 pagos de la misma deuda aceptados`);
  check(p, { 'la misma deuda se cobra una sola vez': (n) => n <= 1 });
}
