// umbrales del requerimiento (seccion 5 del informe)
// consultas e inicio de sesion: p95 < 800 ms; dinero: p95 < 1.5 s; fallas: menos del 1 %
const CONSULTAS = ['login', 'saldo_perfil', 'movimientos', 'contactos', 'deudas', 'otras'];
const DINERO = ['transferencia', 'recarga', 'pago'];

function umbrales(consulta, dinero) {
  const lista = {
    'http_req_duration{tipo:consulta}': [`p(95)<${consulta}`],
    'http_req_duration{tipo:dinero}': [`p(95)<${dinero}`],
    http_req_failed: ['rate<0.01'],
  };
  // una linea por operacion para que el resumen muestre el p95 de cada una
  for (const op of CONSULTAS) lista[`http_req_duration{op:${op}}`] = [`p(95)<${consulta}`];
  for (const op of DINERO) lista[`http_req_duration{op:${op},tipo:dinero}`] = [`p(95)<${dinero}`];
  return lista;
}

export const HORA_PUNTA = umbrales(800, 1500);

// pico de la campaña: "degradacion razonable" no trae numero.
// supuesto: se acepta hasta el doble de tiempo; las fallas siguen en menos del 1 %
export const CAMPANA = umbrales(1600, 3000);

export const ESTADISTICAS = ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'max', 'count'];
