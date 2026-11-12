# cpu, memoria e hilos de un proceso cada segundo, en un csv (el script del enunciado mas los hilos).
# uso: python monitor.py <pid> <archivo.csv>
# se detiene solo cuando aparece <archivo.csv>.fin (lo crea correr.sh al terminar k6)
import csv
import os
import sys
import time

import psutil

proceso = psutil.Process(int(sys.argv[1]))
archivo = sys.argv[2]

with open(archivo, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["hora", "epoch", "cpu_%", "memoria_MB", "hilos"])
    while not os.path.exists(archivo + ".fin"):
        cpu = proceso.cpu_percent(interval=1)
        w.writerow([time.strftime("%H:%M:%S"), int(time.time()), cpu,
                    round(proceso.memory_info().rss / 1e6, 1), proceso.num_threads()])
        f.flush()
