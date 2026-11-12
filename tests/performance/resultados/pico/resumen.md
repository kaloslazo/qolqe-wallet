# Prueba de pico

```
inicio 2026-11-11 21:06:49
fin    2026-11-11 21:32:19
```

## Por tramo estable (mismos VUs al menos 90 s)

| minutos | VUs | peticiones | pet/s | sesiones/min | p95 login | p95 consultas | p95 dinero | errores % | CPU Qolqe prom / máx | memoria máx MB | hilos máx | CPU k6 máx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.0–4.0 | 100 | 804 | 6.6 | 54.0 | 56 | 52 | 131 | 0.00 | 8 / 27 | 66 | 8 | 7 |
| 9.0–19.1 | 300 | 12110 | 20.0 | 165.8 | 56 | 48 | 127 | 0.00 | 20 / 59 | 70 | 12 | 11 |
| 21.6–24.2 | 100 | 1027 | 6.8 | 54.1 | 52 | 48 | 127 | 0.00 | 8 / 26 | 70 | 9 | 12 |

Tiempos en ms. Umbrales de hora punta: consultas y login p95 < 800, dinero p95 < 1500, errores < 1 %.

## Por operación (toda la prueba)

| operación | peticiones | p50 | p95 | p99 | máx | errores % |
|---|---|---|---|---|---|---|
| login | 2892 | 47 | 56 | 88 | 287 | 0.00 |
| saldo_perfil | 5195 | 4 | 5 | 7 | 127 | 0.00 |
| movimientos | 2643 | 20 | 28 | 45 | 278 | 0.00 |
| contactos | 1699 | 4 | 6 | 10 | 32 | 0.00 |
| deudas | 1769 | 4 | 6 | 8 | 144 | 0.00 |
| otras | 1710 | 4 | 6 | 8 | 121 | 0.00 |
| transferencia | 2524 | 95 | 131 | 137 | 284 | 0.00 |
| recarga | 1733 | 8 | 12 | 16 | 147 | 0.00 |
| pago | 680 | 7 | 11 | 14 | 56 | 0.00 |

## Dinero: antes y después

```
OK    transferencias con salida y entrada: 2524 transferencias, 0 con movimientos que no cuadran
OK    saldo = saldo anterior + movimientos: 0 cuentas descuadradas []
OK    deudas pagadas una sola vez: 0 deudas con mas de un pago
OK    codigos de operacion unicos: 0 codigos repetidos
OK    sin saldos negativos: 0 cuentas en negativo
OK    operaciones en la bd = 201 recibidos por k6: bd: 4937, k6: 4937
```
