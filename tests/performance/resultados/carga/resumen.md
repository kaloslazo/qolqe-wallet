# Prueba de carga

```
inicio 2026-11-11 20:42:24
fin    2026-11-11 21:05:55
```

## Por tramo estable (mismos VUs al menos 90 s)

| minutos | VUs | peticiones | pet/s | sesiones/min | p95 login | p95 consultas | p95 dinero | errores % | CPU Qolqe prom / máx | memoria máx MB | hilos máx | CPU k6 máx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.0–22.0 | 100 | 7999 | 6.7 | 55.4 | 56 | 51 | 126 | 0.00 | 8 / 41 | 67 | 9 | 4 |

Tiempos en ms. Umbrales de hora punta: consultas y login p95 < 800, dinero p95 < 1500, errores < 1 %.

## Mesetas largas, cada 5 minutos

| minutos | VUs | peticiones | pet/s | sesiones/min | p95 login | p95 consultas | p95 dinero | errores % | CPU Qolqe prom / máx | memoria máx MB | hilos máx | CPU k6 máx |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2.0–7.0 | 100 | 1996 | 6.7 | 54.0 | 59 | 52 | 126 | 0.00 | 8 / 41 | 67 | 9 | 4 |
| 7.0–12.0 | 100 | 2011 | 6.7 | 56.0 | 56 | 51 | 123 | 0.00 | 8 / 32 | 67 | 8 | 4 |
| 12.0–17.0 | 100 | 1971 | 6.6 | 55.2 | 56 | 51 | 127 | 0.00 | 8 / 39 | 67 | 8 | 4 |
| 17.0–22.0 | 100 | 2014 | 6.7 | 56.4 | 55 | 52 | 127 | 0.00 | 8 / 26 | 67 | 8 | 4 |

## Por operación (toda la prueba)

| operación | peticiones | p50 | p95 | p99 | máx | errores % |
|---|---|---|---|---|---|---|
| login | 1240 | 49 | 56 | 87 | 266 | 0.00 |
| saldo_perfil | 2210 | 4 | 5 | 7 | 55 | 0.00 |
| movimientos | 1126 | 22 | 27 | 46 | 187 | 0.00 |
| contactos | 748 | 5 | 6 | 8 | 38 | 0.00 |
| deudas | 696 | 4 | 6 | 8 | 13 | 0.00 |
| otras | 743 | 4 | 6 | 10 | 48 | 0.00 |
| transferencia | 1107 | 93 | 131 | 138 | 142 | 0.00 |
| recarga | 727 | 9 | 13 | 18 | 76 | 0.00 |
| pago | 272 | 8 | 11 | 12 | 14 | 0.00 |

## Dinero: antes y después

```
OK    transferencias con salida y entrada: 1107 transferencias, 0 con movimientos que no cuadran
OK    saldo = saldo anterior + movimientos: 0 cuentas descuadradas []
OK    deudas pagadas una sola vez: 0 deudas con mas de un pago
OK    codigos de operacion unicos: 0 codigos repetidos
OK    sin saldos negativos: 0 cuentas en negativo
OK    operaciones en la bd = 201 recibidos por k6: bd: 2106, k6: 2106
```
