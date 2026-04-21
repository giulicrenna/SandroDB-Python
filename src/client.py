# -*- coding: utf-8 -*-
"""
SandroClient
=============
Cliente Python para SandroDB server.

Ofrece dos niveles de uso:

1. **Bajo nivel** — ``send_command(cmd)``
   Envia cualquier comando SandroDB como string y devuelve la respuesta.

2. **Alto nivel** — metodos tipados (``login``, ``create_db``, ``insert``, …)
   Wrappers convenientes sobre los comandos del interprete.

Ejemplo minimo
--------------
    from src.client import SandroClient

    client = SandroClient(host="localhost", port=65432)
    client.connect()

    print(client.login("root", "root"))
    print(client.create_db("demo"))
    print(client.use_db("demo"))
    print(client.create_scheme("users", "str", "str", overwrite=True, size_mb=64))
    print(client.insert("users", "alice", "admin"))
    print(client.get("users", "alice"))

    client.disconnect()
"""

from __future__ import annotations

import threading
import time
from queue import Queue, Empty
from typing import Optional

from FastSocket import SocketConfig, FastSocketClient

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DEFAULT_HOST: str = "localhost"
DEFAULT_PORT: int = 65432
DEFAULT_TIMEOUT: float = 10.0


# ---------------------------------------------------------------------------
# SandroClient
# ---------------------------------------------------------------------------

class SandroClient:
    """
    Cliente TCP para SandroDB.

    Parameters
    ----------
    host : str
        Host o IP del servidor SandroDB.
    port : int
        Puerto TCP del servidor.
    timeout : float
        Segundos maximos de espera por respuesta del servidor.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

        self._response_queue: Queue[str] = Queue()
        self._connected = False
        self._lock = threading.Lock()

        config = SocketConfig(host=host, port=port)
        self._socket_client = FastSocketClient(config)
        self._socket_client.on_new_message(self._on_message)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_message(self, data: str) -> None:
        """Recibe cada respuesta del servidor como str y la encola."""
        self._response_queue.put(data)

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Establece la conexion con el servidor.

        ``FastSocketClient.start()`` conecta en un thread de fondo, por lo
        que esperamos hasta confirmar que el socket tiene un peer valido
        antes de marcar el cliente como conectado.
        """
        self._socket_client.start()

        deadline = time.time() + self.timeout
        while time.time() < deadline:
            try:
                self._socket_client.sock.getpeername()
                self._connected = True
                return
            except OSError:
                time.sleep(0.05)

        raise ConnectionError(
            f"Could not connect to {self.host}:{self.port} within {self.timeout}s"
        )

    def disconnect(self) -> None:
        """Cierra la conexion limpiamente."""
        self._connected = False

    @property
    def connected(self) -> bool:
        """``True`` si la conexion esta activa."""
        return self._connected and self._socket_client.is_alive()

    # ------------------------------------------------------------------
    # Low-level API
    # ------------------------------------------------------------------

    def send_command(self, command: str, timeout: Optional[float] = None) -> str:
        """
        Envia un comando SandroDB crudo y devuelve la respuesta del servidor.

        Parameters
        ----------
        command : str
            Comando exactamente como se escribiria en el interprete.
            Ejemplo: ``"insert_into users alice admin"``
        timeout : float | None
            Segundos de espera. Si es ``None`` usa el timeout del cliente.

        Returns
        -------
        str
            Respuesta del servidor, o un mensaje de error si hay timeout.

        Raises
        ------
        RuntimeError
            Si el cliente no esta conectado.
        """
        if not self._connected:
            raise RuntimeError("Client is not connected. Call connect() first.")

        with self._lock:
            # Vaciar respuestas previas no consumidas
            while not self._response_queue.empty():
                self._response_queue.get_nowait()

            self._socket_client.send_to_server(command)

            wait = timeout if timeout is not None else self.timeout
            try:
                return self._response_queue.get(timeout=wait)
            except Empty:
                return f"[TIMEOUT] No response after {wait}s for command: {command!r}"

    # ------------------------------------------------------------------
    # High-level API
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> str:
        """Autentica al usuario en el servidor."""
        return self.send_command(f"login {username} {password}")

    def logout(self) -> str:
        """Cierra la sesion del usuario actual."""
        return self.send_command("logout")

    def create_db(self, name: str) -> str:
        """Crea una nueva base de datos."""
        return self.send_command(f"create_db {name}")

    def use_db(self, name: str) -> str:
        """Selecciona la base de datos activa."""
        return self.send_command(f"use_db {name}")

    def show_databases(self) -> str:
        """Lista todas las bases de datos disponibles."""
        return self.send_command("show_databases")

    def create_scheme(
        self,
        name: str,
        key_type: str,
        val_type: str,
        overwrite: bool = True,
        size_mb: int = 64,
    ) -> str:
        """
        Crea un scheme dentro de la base de datos activa.

        Parameters
        ----------
        name : str
            Nombre del scheme.
        key_type : str
            Tipo de las claves. Valores validos: ``str``, ``int``, ``float``, etc.
        val_type : str
            Tipo de los valores.
        overwrite : bool
            Si es ``True`` permite sobreescribir claves existentes.
        size_mb : int
            Tamano maximo del scheme en megabytes.
        """
        ow = "True" if overwrite else "False"
        return self.send_command(f"create_scheme {name} {key_type} {val_type} {ow} {size_mb}")

    def show_schemes(self) -> str:
        """Lista los schemes de la base de datos activa."""
        return self.send_command("show_schemes")

    def delete_scheme(self, name: str) -> str:
        """Elimina un scheme de la base de datos activa."""
        return self.send_command(f"del_scheme {name}")

    def insert(self, scheme: str, key: str, value: str) -> str:
        """
        Inserta o actualiza un registro en un scheme.

        Parameters
        ----------
        scheme : str
            Nombre del scheme destino.
        key : str
            Clave del registro.
        value : str
            Valor del registro. Puede ser JSON para valores de tipo ``dict``.
        """
        return self.send_command(f"insert_into {scheme} {key} {value}")

    def get(self, scheme: str, key: str) -> str:
        """Recupera el valor de una clave en un scheme."""
        return self.send_command(f"get_registry {scheme} {key}")

    def get_all(self) -> str:
        """Recupera todos los registros de todos los schemes."""
        return self.send_command("get_all_registry")

    def show_users(self) -> str:
        """Lista los usuarios registrados (requiere READ_PRIVILEGE)."""
        return self.send_command("show_users")

    def help(self) -> str:
        """Devuelve la ayuda del servidor."""
        return self.send_command("help")
