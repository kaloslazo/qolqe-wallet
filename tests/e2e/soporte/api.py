"""Cliente HTTP de la API de Qolqe para preparar datos y verificar efectos que la UI no muestra."""
import requests

USUARIOS = {
    "Ana": ("987654321", "4826"),
    "Bruno": ("912345678", "7391"),
    "Carla": ("956781234", "5917"),
    "Diego": ("998877665", "3604"),
}


class ApiQolqe:
    def __init__(self, url_base: str):
        self.url_base = url_base.rstrip("/")
        self.http = requests.Session()

    def _url(self, ruta: str) -> str:
        return f"{self.url_base}{ruta}"

    def esta_arriba(self) -> bool:
        try:
            return self.http.get(self._url("/api/salud"), timeout=2).ok
        except requests.RequestException:
            return False

    # ---- API de soporte para pruebas (QOLQE_MODO_PRUEBA=1)
    def reiniciar(self) -> None:
        self.http.post(self._url("/api/pruebas/reiniciar"), timeout=60).raise_for_status()

    def fijar_reloj(self, ahora: str) -> None:
        self.http.put(self._url("/api/pruebas/reloj"), json={"ahora": ahora}, timeout=10).raise_for_status()

    def avanzar_reloj(self, minutos: int) -> None:
        self.http.put(self._url("/api/pruebas/reloj"), json={"avanzar_minutos": minutos}, timeout=10).raise_for_status()

    def hora_real(self) -> None:
        self.http.delete(self._url("/api/pruebas/reloj"), timeout=10)

    def notificaciones(self, celular: str) -> list[dict]:
        respuesta = self.http.get(self._url("/api/pruebas/notificaciones"), params={"celular": celular}, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()

    # ---- API del producto
    def login(self, usuario: str) -> dict:
        celular, pin = USUARIOS[usuario]
        respuesta = self.http.post(self._url("/api/auth/login"), json={"celular": celular, "pin": pin}, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()

    def cambiar_limite(self, token: str, monto: int) -> dict:
        respuesta = self.http.put(self._url("/api/limites"), json={"limite_diario": monto},
                                  headers={"Authorization": f"Bearer {token}"}, timeout=10)
        respuesta.raise_for_status()
        return respuesta.json()
