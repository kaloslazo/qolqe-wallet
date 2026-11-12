/** Pasos del núcleo común (registro, sesión, cuenta, transferencias) y pasos extra de G5. */
import { expect, type APIRequestContext } from '@playwright/test';
import { DataTable } from 'playwright-bdd';
import { Given, Sesion, Then, USUARIOS, When, cuerpo, sesionDe } from './fixtures';

const PIN_ERRADO = '0000';

async function smsDe(request: APIRequestContext, celular: string): Promise<string[]> {
  const r = await request.get('/api/pruebas/notificaciones', { params: { celular } });
  return ((await r.json()) as unknown[]).map((n) => JSON.stringify(n));
}

/** La sesión del escenario si es de ese usuario; si no, una sesión aparte. */
async function sesionPara(sesion: Sesion, request: APIRequestContext, nombre: string) {
  return sesion.usuario === nombre ? sesion : sesionDe(request, nombre);
}

/** Valor de un campo anidado ("destinatario.nombre") de un objeto. */
function campo(datos: any, ruta: string) {
  return ruta.split('.').reduce((valor, parte) => valor?.[parte], datos);
}

// ------------------------------------------------------------------------------------- registro
When(
  'me registro con DNI {string}, celular {string} y PIN {string}',
  async ({ sesion }, dni: string, celular: string, pin: string) => {
    sesion.respuesta = await sesion.cruda('post', '/api/usuarios', undefined, {
      dni, celular, pin, nombres: 'Lucía Fernández Rojas',
    });
  },
);

When(
  'me registro con DNI {string}, celular {string}, PIN {string} y correo {string}',
  async ({ sesion }, dni: string, celular: string, pin: string, correo: string) => {
    sesion.respuesta = await sesion.cruda('post', '/api/usuarios', undefined, {
      dni, celular, pin, correo, nombres: 'Lucía Fernández Rojas',
    });
  },
);

Then('la respuesta tiene el código HTTP {int}', async ({ sesion }, codigo: number) => {
  expect(sesion.respuesta!.status(), await sesion.respuesta!.text()).toBe(codigo);
});

Then('el celular {word} recibe un SMS que contiene {string}', async ({ request }, celular: string, texto: string) => {
  const sms = ((await (await request.get('/api/pruebas/notificaciones', { params: { celular } })).json()) as unknown[])
    .map((n) => JSON.stringify(n));
  expect(sms.some((s) => s.includes(texto)), sms.join('\n')).toBeTruthy();
});

Then(
  'al iniciar sesión con el celular {word} y el PIN {word} mi saldo es S\\/ {word}',
  async ({ sesion }, celular: string, pin: string, saldo: string) => {
    await sesion.loginCon(celular, pin);
    expect((await (await sesion.api('get', '/api/cuentas/me/saldo')).json()).saldo).toBe(saldo);
  },
);

When('me registro con nombres de {int} caracteres', async ({ sesion }, largo: number) => {
  sesion.respuesta = await sesion.cruda('post', '/api/usuarios', undefined, {
    dni: '45678912', celular: '987000111', pin: '4826', nombres: 'a'.repeat(largo),
  });
});

// con el PIN de los registros de prueba: si la cuenta existiera, el ingreso funcionaría
Then('el celular {word} sigue sin cuenta', async ({ sesion }, celular: string) => {
  const r = await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin: '4826' });
  expect(r.status(), await r.text()).toBe(401);
  expect((await r.json()).codigo).toBe('CREDENCIALES_INVALIDAS');
});

Then('el celular {word} no recibe un SMS que contiene {string}', async ({ request }, celular: string, texto: string) => {
  const sms = await smsDe(request, celular);
  expect(sms.filter((s) => s.includes(texto)), sms.join('\n')).toHaveLength(0);
});

Then(
  'el celular {word} recibe {int} SMS que contienen {string}',
  async ({ request }, celular: string, n: number, texto: string) => {
    const sms = await smsDe(request, celular);
    expect(sms.filter((s) => s.includes(texto)), sms.join('\n')).toHaveLength(n);
  },
);

// ------------------------------------------------------------------------------------- sesión
When('inicio sesión con el celular {word} y el PIN {word}', async ({ sesion }, celular: string, pin: string) => {
  sesion.respuesta = await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin });
  if (sesion.respuesta.ok()) {
    sesion.cred = { celular, pin };
    sesion.token = (await sesion.respuesta.json()).access_token;
  }
});

Then('recibo un token válido por {int} minutos', async ({ sesion }, minutos: number) => {
  const r = sesion.respuesta!;
  expect(r.status(), await r.text()).toBe(200);
  const datos = await r.json();
  expect(datos.access_token).toBeTruthy();
  expect(datos.expires_in).toBe(minutos * 60);
});

Given('que ya fallé {int} veces el PIN del celular {word}', async ({ sesion }, veces: number, celular: string) => {
  for (let i = 0; i < veces; i++) {
    const r = await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin: PIN_ERRADO });
    expect(r.status()).toBe(401);
  }
});

Given('que la cuenta del celular {word} quedó bloqueada', async ({ sesion }, celular: string) => {
  let ultima = 0;
  for (let i = 0; i < 3; i++) {
    ultima = (await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin: PIN_ERRADO })).status();
  }
  expect(ultima).toBe(423);
});

When('cierro sesión', async ({ sesion }) => {
  sesion.tokens = [sesion.token!];
  expect((await sesion.cruda('post', '/api/auth/logout', sesion.token)).status()).toBe(204);
});

Then('mi token anterior responde {int}', async ({ sesion }, codigo: number) => {
  expect((await sesion.cruda('get', '/api/cuentas/me', sesion.tokens[0])).status()).toBe(codigo);
});

Given('que inicié sesión como {word} en dos equipos', async ({ sesion }, nombre: string) => {
  await sesion.login(nombre);
  const primero = sesion.token!;
  await sesion.login(nombre);
  sesion.tokens = [primero, sesion.token!];
});

When('cierro sesión en el primer equipo', async ({ sesion }) => {
  expect((await sesion.cruda('post', '/api/auth/logout', sesion.tokens[0])).status()).toBe(204);
});

Then('el segundo equipo sigue consultando mi saldo', async ({ sesion }) => {
  expect((await sesion.cruda('get', '/api/cuentas/me/saldo', sesion.tokens[1])).status()).toBe(200);
});

When(
  'inicio sesión con el celular {word}, el PIN {word} y el dispositivo {word}',
  async ({ sesion }, celular: string, pin: string, dispositivo: string) => {
    sesion.respuesta = await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin, dispositivo_id: dispositivo });
  },
);

When('consulto mis sesiones activas', async ({ sesion }) => {
  sesion.respuesta = await sesion.api('get', '/api/seguridad/sesiones');
});

Then('veo mi sesión actual, que vence a los {int} minutos', async ({ sesion }, minutos: number) => {
  const sesiones: any[] = await sesion.respuesta!.json();
  const actual = sesiones.find((s) => s.actual);
  expect(actual, JSON.stringify(sesiones)).toBeTruthy();
  const duracion = Date.parse(actual.expira_en) - Date.parse(actual.iniciada_en);
  expect(duracion).toBe(minutos * 60_000);
});

// el token que recibí al ingresar, sin el re-login automático
When('consulto mi saldo sin volver a iniciar sesión', async ({ sesion }) => {
  sesion.respuesta = await sesion.cruda('get', '/api/cuentas/me/saldo', sesion.token);
});

Then('mi token sigue consultando mi saldo', async ({ sesion }) => {
  expect((await sesion.cruda('get', '/api/cuentas/me/saldo', sesion.token)).status()).toBe(200);
});

let comparadas: string[] = [];

When(
  'inicio sesión con el celular {word} y el PIN {word}, y luego con el celular {word} y el PIN {word}',
  async ({ sesion }, celular1: string, pin1: string, celular2: string, pin2: string) => {
    comparadas = [];
    for (const [celular, pin] of [[celular1, pin1], [celular2, pin2]]) {
      const r = await sesion.cruda('post', '/api/auth/login', undefined, { celular, pin });
      comparadas.push(`${r.status()} ${await r.text()}`);
    }
  },
);

Then('las dos respuestas son idénticas', async () => {
  expect(comparadas[0]).toBe(comparadas[1]);
});

// ------------------------------------------------------------------------------------- cuenta
When('consulto mi saldo', async ({ sesion }) => {
  sesion.respuesta = await sesion.api('get', '/api/cuentas/me/saldo');
});

Then('la moneda es {string}', async ({ sesion }, moneda: string) => {
  expect((await sesion.respuesta!.json()).moneda).toBe(moneda);
});

When('consulto mi perfil', async ({ sesion }) => {
  sesion.respuesta = await sesion.api('get', '/api/cuentas/me');
});

Then('el DNI se muestra con solo los últimos 4 dígitos', async ({ sesion }) => {
  expect((await sesion.respuesta!.json()).dni).toMatch(/^\*{4}\d{4}$/);
});

When('consulto el saldo sin token', async ({ sesion }) => {
  sesion.respuesta = await sesion.cruda('get', '/api/cuentas/me/saldo');
});

When('cambio mi correo a {string}', async ({ sesion }, correo: string) => {
  sesion.respuesta = await sesion.api('put', '/api/cuentas/me', { correo });
});

When('intento cambiar mi celular a {string}', async ({ sesion }, celular: string) => {
  sesion.respuesta = await sesion.api('put', '/api/cuentas/me', { celular });
});

Then('mi perfil sigue con el celular {word}', async ({ sesion }, celular: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me')).json()).celular).toBe(celular);
});

Given('que mi saldo es S\\/ {word}', async ({ sesion }, saldo: string) => {
  const r = await sesion.request.put('/api/pruebas/saldo', { data: { celular: sesion.celular, saldo } });
  expect(r.ok(), await r.text()).toBeTruthy();
});

When('cierro mi cuenta con el PIN {word}', async ({ sesion }, pin: string) => {
  sesion.respuesta = await sesion.api('post', '/api/cuentas/me/cierre', { pin });
});

Given('que cerré mi cuenta con el PIN {word}', async ({ sesion }, pin: string) => {
  const r = await sesion.api('post', '/api/cuentas/me/cierre', { pin });
  expect(r.status(), await r.text()).toBe(204);
});

Then('mi saldo se actualizó el {string}', async ({ sesion }, fecha: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me/saldo')).json()).actualizado_en).toMatch(new RegExp(`^${fecha}`));
});

Then(
  'mi perfil muestra los nombres {string}, el celular {word} y el correo {string}',
  async ({ sesion }, nombres: string, celular: string, correo: string) => {
    const perfil = await sesion.respuesta!.json();
    expect({ nombres: perfil.nombres, celular: perfil.celular, correo: perfil.correo }).toEqual({ nombres, celular, correo });
  },
);

Then('el perfil no muestra el DNI {string} ni el PIN', async ({ sesion }, dni: string) => {
  const texto = await sesion.respuesta!.text();
  expect(texto).not.toContain(dni);
  expect(Object.keys(JSON.parse(texto)).filter((k) => k.includes('pin'))).toEqual([]);
});

When('cambio mis nombres por unos de {int} caracteres', async ({ sesion }, largo: number) => {
  sesion.respuesta = await sesion.api('put', '/api/cuentas/me', { nombres: 'a'.repeat(largo) });
});

When('intento cambiar mi DNI a {string}', async ({ sesion }, dni: string) => {
  sesion.respuesta = await sesion.api('put', '/api/cuentas/me', { dni });
});

Then('mi perfil sigue con el DNI {string}', async ({ sesion }, dni: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me')).json()).dni).toBe(dni);
});

Then('mi perfil sigue con el correo {string}', async ({ sesion }, correo: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me')).json()).correo).toBe(correo);
});

Then('mi perfil sigue con los nombres {string}', async ({ sesion }, nombres: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me')).json()).nombres).toBe(nombres);
});

Then('mi cuenta sigue {word}', async ({ sesion }, estado: string) => {
  expect((await (await sesion.api('get', '/api/cuentas/me')).json()).estado).toBe(estado);
});

// la solicitud la crea el otro usuario desde su lista de contactos (G4)
Given('que {word} me solicitó S\\/ {word}', async ({ sesion, request }, nombre: string, monto: string) => {
  const otro = await sesionDe(request, nombre);
  const contactos: any[] = (await (await otro.api('get', '/api/contactos')).json()).contactos;
  const contacto = contactos.find((c) => c.celular === sesion.celular);
  expect(contacto, `${nombre} no me tiene como contacto`).toBeTruthy();
  const r = await otro.api('post', '/api/solicitudes', { contacto_id: contacto.id, monto, motivo: 'Préstamo del mes' });
  expect(r.status(), await r.text()).toBe(201);
});

Then('ninguno de mis dos equipos puede consultar mi saldo', async ({ sesion }) => {
  for (const token of sesion.tokens) {
    expect((await sesion.cruda('get', '/api/cuentas/me/saldo', token)).status()).toBe(401);
  }
});

Then('al volver a iniciar sesión el resultado es {string}', async ({ sesion }, codigo: string) => {
  const r = await sesion.cruda('post', '/api/auth/login', undefined, sesion.cred);
  expect(r.status(), await r.text()).toBeGreaterThanOrEqual(400);
  expect((await r.json()).codigo).toBe(codigo);
});

// ------------------------------------------------------------------------------------- transferencias
Then('la transferencia tiene un código de operación', async ({ sesion }) => {
  expect((await cuerpo(sesion.respuesta!)).codigo_operacion).toBeTruthy();
});

When('transfiero S\\/ {word} al CCI {word}', async ({ sesion }, monto: string, cci: string) => {
  sesion.respuesta = await sesion.api('post', '/api/transferencias', { tipo: 'INTERBANCARIA', cci, monto });
});

When('simulo la comisión de S\\/ {word} a otro banco', async ({ sesion }, monto: string) => {
  sesion.respuesta = await sesion.api('get', `/api/transferencias/comision?monto=${monto}&tipo=INTERBANCARIA`);
});

Then('la comisión es S\\/ {word} y el total S\\/ {word}', async ({ sesion }, comision: string, total: string) => {
  const datos = await sesion.respuesta!.json();
  expect(datos.comision).toBe(comision);
  expect(datos.total).toBe(total);
});

When(
  'envío {int} transferencias simultáneas de S\\/ {word} al celular {word}',
  async ({ sesion }, n: number, monto: string, celular: string) => {
    await Promise.all(
      Array.from({ length: n }, () => sesion.api('post', '/api/transferencias', { celular_destino: celular, monto })),
    );
  },
);

Then('lo usado hoy no supera S\\/ {word}', async ({ sesion }, tope: string) => {
  expect(Number((await sesion.limites()).usado_hoy)).toBeLessThanOrEqual(Number(tope));
});

async function idDeContacto(dueno: Sesion, alias: string) {
  const contactos: any[] = (await (await dueno.api('get', '/api/contactos')).json()).contactos;
  const contacto = contactos.find((c) => c.alias === alias);
  expect(contacto, `No existe el contacto ${alias}`).toBeTruthy();
  return contacto.id;
}

When('transfiero S\\/ {word} a mi contacto {string}', async ({ sesion }, monto: string, alias: string) => {
  sesion.respuesta = await sesion.api('post', '/api/transferencias', { contacto_id: await idDeContacto(sesion, alias), monto });
});

When(
  'transfiero S\\/ {word} al contacto {string} de {word}',
  async ({ sesion, request }, monto: string, alias: string, dueno: string) => {
    const id = await idDeContacto(await sesionDe(request, dueno), alias);
    sesion.respuesta = await sesion.api('post', '/api/transferencias', { contacto_id: id, monto });
  },
);

When(
  'transfiero S\\/ {word} al celular {word} con una descripción de {int} caracteres',
  async ({ sesion }, monto: string, celular: string, largo: number) => {
    sesion.respuesta = await sesion.api('post', '/api/transferencias', {
      celular_destino: celular, monto, descripcion: 'd'.repeat(largo),
    });
  },
);

Then('el saldo de {word} es S\\/ {word}', async ({ sesion, request }, nombre: string, saldo: string) => {
  const otra = await sesionPara(sesion, request, nombre);
  expect((await (await otra.api('get', '/api/cuentas/me/saldo')).json()).saldo).toBe(saldo);
});

/** Movimiento del usuario con el código de la última transferencia (de sus 20 más recientes). */
async function movimientoDe(sesion: Sesion, request: APIRequestContext, nombre: string) {
  const codigo = (await cuerpo(sesion.respuesta!)).codigo_operacion;
  expect(codigo, 'la transferencia no tiene código').toBeTruthy();
  const otra = await sesionPara(sesion, request, nombre);
  const movimientos: any[] = await (await otra.api('get', '/api/movimientos/recientes?limite=20')).json();
  const movimiento = movimientos.find((m) => m.codigo_operacion === codigo);
  expect(movimiento, `${nombre} no tiene un movimiento ${codigo}`).toBeTruthy();
  return movimiento;
}

Then(
  'el movimiento de {word} con el código de la transferencia es {word} por S\\/ {word}',
  async ({ sesion, request }, nombre: string, tipo: string, importe: string) => {
    const movimiento = await movimientoDe(sesion, request, nombre);
    expect({ tipo: movimiento.tipo, importe: movimiento.importe }).toEqual({ tipo, importe });
  },
);

Then(
  'el movimiento de {word} con el código de la transferencia muestra la contraparte {string}',
  async ({ sesion, request }, nombre: string, contraparte: string) => {
    expect((await movimientoDe(sesion, request, nombre)).contraparte).toBe(contraparte);
  },
);

Then('el comprobante muestra', async ({ sesion }, tabla: DataTable) => {
  const comprobante = await cuerpo(sesion.respuesta!);
  for (const [ruta, valor] of Object.entries(tabla.rowsHash())) {
    expect(String(campo(comprobante, ruta)), `${ruta} en ${JSON.stringify(comprobante)}`).toBe(valor);
  }
});

Then('el comprobante tiene la fecha {string}', async ({ sesion }, fecha: string) => {
  expect((await cuerpo(sesion.respuesta!)).fecha).toMatch(new RegExp(`^${fecha}`));
});

let codigos: string[] = [];

// el reloj se fija en el mismo instante antes de cada una: las dos caen en el mismo segundo
When(
  'transfiero S\\/ {word} al celular {word} y S\\/ {word} al celular {word} en el mismo segundo',
  async ({ sesion, request }, monto1: string, celular1: string, monto2: string, celular2: string) => {
    codigos = [];
    for (const [monto, celular] of [[monto1, celular1], [monto2, celular2]]) {
      expect((await request.put('/api/pruebas/reloj', { data: { ahora: '2026-11-10T10:05:00' } })).ok()).toBeTruthy();
      const r = await sesion.api('post', '/api/transferencias', { celular_destino: celular, monto });
      expect(r.status(), await r.text()).toBe(201);
      codigos.push((await r.json()).codigo_operacion);
    }
  },
);

Then('las dos transferencias tienen códigos de operación distintos', async () => {
  expect(codigos[0], codigos.join(' y ')).not.toBe(codigos[1]);
});

When('simulo la comisión de S\\/ {word} a otro usuario Qolqe', async ({ sesion }, monto: string) => {
  sesion.respuesta = await sesion.api('get', `/api/transferencias/comision?monto=${monto}&tipo=QOLQE`);
});

When('{word} transfiere S\\/ {word} al celular {word}', async ({ request }, nombre: string, monto: string, celular: string) => {
  const otro = await sesionDe(request, nombre);
  const r = await otro.api('post', '/api/transferencias', { celular_destino: celular, monto });
  expect(r.status(), await r.text()).toBe(201);
});

// ------------------------------------------------------------------------------------- G5 extra
When('consulto mis alertas', async ({ sesion }) => {
  sesion.respuesta = await sesion.api('get', '/api/limites/alertas');
});

Then(
  'la alerta de {word} con umbral S\\/ {word} tiene un gasto de hoy de S\\/ {word}',
  async ({ sesion }, tipo: string, umbral: string, gasto: string) => {
    expect((await sesion.alerta(tipo, umbral)).gasto_hoy).toBe(gasto);
  },
);

Given('que eliminé la alerta de {word} con umbral S\\/ {word}', async ({ sesion }, tipo: string, umbral: string) => {
  const a = await sesion.alerta(tipo, umbral);
  expect((await sesion.api('delete', `/api/limites/alertas/${a.id}`)).status()).toBe(204);
});

async function solicitudRecibidaDe(sesion: Sesion, nombre: string) {
  const recibidas: any[] = (await (await sesion.api('get', '/api/solicitudes')).json()).recibidas;
  const solicitud = recibidas.find((s) => s.solicitante.celular === USUARIOS[nombre].celular);
  expect(solicitud, `No tengo una solicitud de ${nombre}`).toBeTruthy();
  return solicitud;
}

When('acepto la solicitud de dinero que me envió {word}', async ({ sesion }, nombre: string) => {
  const solicitud = await solicitudRecibidaDe(sesion, nombre);
  sesion.respuesta = await sesion.api('post', `/api/solicitudes/${solicitud.id}/aceptar`);
});

Then('la solicitud de dinero de {word} está {word}', async ({ sesion }, nombre: string, estado: string) => {
  expect((await solicitudRecibidaDe(sesion, nombre)).estado).toBe(estado);
});

// ------------------------------------------------------------------------------------- concurrencia
let simultaneas: number[] = [];

When('{int} visitantes se registran a la vez con el celular {string}', async ({ sesion }, n: number, celular: string) => {
  const respuestas = await Promise.all(
    Array.from({ length: n }, () =>
      sesion.cruda('post', '/api/usuarios', undefined, { dni: '45678912', celular, pin: '4826', nombres: 'Lucía Fernández' }),
    ),
  );
  simultaneas = respuestas.map((r) => r.status()).sort();
});

Then('una respuesta es 201 y las demás son 409 con {string}', async ({}, _codigo: string) => {
  expect(simultaneas).toEqual([201, ...Array(simultaneas.length - 1).fill(409)]);
});
