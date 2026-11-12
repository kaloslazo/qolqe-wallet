# Prueba de humo

```
inicio 2026-11-11 21:33:08
fin    2026-11-11 21:37:38
```

## Por tramo estable (mismos VUs al menos 90 s)

| minutos | VUs | peticiones | pet/s | sesiones/min | p95 login | p95 consultas | p95 dinero | errores % | CPU Qolqe prom / máx | memoria máx MB | hilos máx | CPU k6 máx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.0–4.5 | 1 | 17 | 0.1 | 0.4 | 60 | 60 | 91 | 0.00 | 0 / 5 | 64 | 6 | 1 |

Tiempos en ms. Umbrales de hora punta: consultas y login p95 < 800, dinero p95 < 1500, errores < 1 %.

## Por operación (toda la prueba)

| operación | peticiones | p50 | p95 | p99 | máx | errores % |
|---|---|---|---|---|---|---|
| login | 3 | 52 | 60 | 60 | 60 | 0.00 |
| saldo_perfil | 7 | 6 | 18 | 18 | 18 | 0.00 |
| movimientos | 3 | 19 | 20 | 20 | 20 | 0.00 |
| contactos | 2 | 7 | 9 | 9 | 9 | 0.00 |
| otras | 2 | 4 | 6 | 6 | 6 | 0.00 |
| transferencia | 1 | 91 | 91 | 91 | 91 | 0.00 |

## Dinero: antes y después

```
OK    transferencias con salida y entrada: 1 transferencias, 0 con movimientos que no cuadran
OK    saldo = saldo anterior + movimientos: 0 cuentas descuadradas []
OK    deudas pagadas una sola vez: 0 deudas con mas de un pago
OK    codigos de operacion unicos: 0 codigos repetidos
OK    sin saldos negativos: 0 cuentas en negativo
OK    operaciones en la bd = 201 recibidos por k6: bd: 1, k6: 1
```
