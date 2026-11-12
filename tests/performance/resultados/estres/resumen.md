# Prueba de estres

```
inicio 2026-11-11 20:11:43
fin    2026-11-11 20:41:14
```

## Por tramo estable (mismos VUs al menos 90 s)

| minutos | VUs | peticiones | pet/s | sesiones/min | p95 login | p95 consultas | p95 dinero | errores % | CPU Qolqe prom / máx | memoria máx MB | hilos máx | CPU k6 máx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1.0–4.0 | 100 | 1177 | 6.5 | 48.3 | 63 | 53 | 125 | 0.00 | 8 / 36 | 67 | 9 | 58 |
| 5.0–8.0 | 300 | 3578 | 19.9 | 152.0 | 61 | 50 | 124 | 0.00 | 21 / 45 | 69 | 10 | 45 |
| 9.0–12.0 | 600 | 7170 | 39.8 | 315.0 | 95 | 51 | 126 | 0.00 | 35 / 77 | 74 | 17 | 47 |
| 13.0–16.0 | 800 | 1785 | 9.9 | 45.0 | 60012 | 60012 | 60010 | 86.44 | 15 / 76 | 302 | 54 | 49 |
| 17.0–20.0 | 1000 | 2405 | 13.4 | 119.0 | 60001 | 60001 | 60001 | 100.00 | 21 / 73 | 423 | 52 | 45 |
| 21.0–24.0 | 1200 | 2987 | 16.6 | 1.3 | 60003 | 60003 | 60001 | 100.00 | 26 / 157 | 593 | 53 | 51 |
| 25.0–28.1 | 1400 | 3562 | 19.2 | 0.0 | 60001 | 60001 | nan | 100.00 | 25 / 107 | 774 | 51 | 42 |

Tiempos en ms. Umbrales de hora punta: consultas y login p95 < 800, dinero p95 < 1500, errores < 1 %.

## Por operación (toda la prueba)

| operación | peticiones | p50 | p95 | p99 | máx | errores % |
|---|---|---|---|---|---|---|
| login | 14106 | 60001 | 60002 | 60013 | 60920 | 80.77 |
| saldo_perfil | 4893 | 4 | 60002 | 60010 | 60360 | 15.39 |
| movimientos | 2366 | 18 | 60002 | 60010 | 60237 | 14.96 |
| contactos | 1635 | 4 | 60002 | 60011 | 60340 | 15.60 |
| deudas | 1606 | 4 | 60002 | 60010 | 60230 | 15.26 |
| otras | 1667 | 4 | 60002 | 60010 | 60157 | 15.00 |
| transferencia | 2474 | 103 | 60002 | 60009 | 60135 | 18.71 |
| recarga | 1637 | 8 | 60002 | 60010 | 60043 | 17.47 |
| pago | 556 | 6 | 13 | 60001 | 60001 | 2.52 |

## Dinero: antes y después

```
OK    transferencias con salida y entrada: 2013 transferencias, 0 con movimientos que no cuadran
OK    saldo = saldo anterior + movimientos: 0 cuentas descuadradas []
OK    deudas pagadas una sola vez: 0 deudas con mas de un pago
OK    codigos de operacion unicos: 0 codigos repetidos
OK    sin saldos negativos: 0 cuentas en negativo
FALLA operaciones en la bd = 201 recibidos por k6: bd: 3910, k6: 3904
```
