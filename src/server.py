# -*- coding: utf-8 -*-
"""
SandroServer
=============
Servidor TCP de SandroDB construido sobre FastSocket 2.0.0.

Cada cliente que se conecta recibe su propio ``Interpreter`` en modo
``server``, lo que garantiza aislamiento de sesion (usuario logueado,
base de datos seleccionada, etc.).

Flujo de un mensaje entrante
-----------------------------
  Cliente  ──send("login root root")──>  FastSocketServer
                                              │
                                        _on_message(queue)
                                              │
                                        Interpreter.add_command_task()
                                              │
                                        output_callback(msg, conn_id)
                                              │
                                        server._send(addr, msg)  ──>  Cliente

Uso minimo
----------
    from src.server import SandroServer
    server = SandroServer(host="0.0.0.0", port=65432)
    server.start()          # bloqueante
"""

from __future__ import annotations

import os
import threading
from typing import Dict, Tuple, Any

from FastSocket import SocketConfig, FastSocketServer
from FastSocket.utils.framing import send_framed

from src.core import Interpreter, InterpreterType, VirtualMemory
from src.logger import Logger

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = 65432


# ---------------------------------------------------------------------------
# SandroServer
# ---------------------------------------------------------------------------

class SandroServer:
    """
    Envuelve ``FastSocketServer`` y gestiona un ``Interpreter`` por conexion.

    Parameters
    ----------
    host : str
        Direccion IP en la que escucha el servidor.
    port : int
        Puerto TCP.
    """

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port

        self._virtual_memory: VirtualMemory = VirtualMemory()

        # addr(str) -> (Interpreter, conn_id)
        self._sessions: Dict[Any, Tuple[Interpreter, int]] = {}
        self._lock = threading.Lock()
        self._conn_counter = 0

        config = SocketConfig(host=host, port=port)
        self._socket_server = FastSocketServer(config)
        self._socket_server.on_new_message(self._on_message)

        self._ensure_data_dir()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_data_dir(self) -> None:
        if not os.path.isdir(".sandro"):
            os.mkdir(".sandro")

    def _next_conn_id(self) -> int:
        self._conn_counter += 1
        return self._conn_counter

    def _get_or_create_session(self, addr: Any) -> Interpreter:
        """Return existing Interpreter for *addr* or spin up a new one."""
        with self._lock:
            if addr in self._sessions:
                return self._sessions[addr][0]

            conn_id = self._next_conn_id()
            self._virtual_memory.add_conn_id(conn_id)

            interp = Interpreter(
                type=InterpreterType.server,
                virtual_memory=self._virtual_memory,
                conn_id=conn_id,
            )

            # Capture addr in closure so each session sends to the right client
            def output_callback(message: str, _cid: int, _addr=addr) -> None:
                self._send_to_client(_addr, message)

            interp.set_output_callback(output_callback)
            interp.start()

            self._sessions[addr] = (interp, conn_id)
            Logger.print_log_normal(f"New session for {addr} (conn_id={conn_id})", "SandroServer")
            return interp

    def _send_to_client(self, addr: Any, message: str) -> None:
        """Envía *message* al cliente identificado por *addr*."""
        with self._socket_server._client_lock:
            clients = list(self._socket_server._client_buffer)
        for client in clients:
            if client.address == addr and client.connected:
                try:
                    send_framed(client.connection, message.encode("utf-8"))
                except Exception as exc:
                    Logger.print_log_error(str(exc), "SandroServer._send_to_client")
                return

    def _close_session(self, addr: Any) -> None:
        with self._lock:
            if addr not in self._sessions:
                return
            interp, _ = self._sessions.pop(addr)

        try:
            interp.at_close()
        except Exception as exc:
            Logger.print_log_error(str(exc), "SandroServer._close_session")
        Logger.print_log_normal(f"Session closed for {addr}", "SandroServer")

    # ------------------------------------------------------------------
    # Message handler (registered with FastSocketServer)
    # ------------------------------------------------------------------

    def _on_message(self, queue) -> None:
        """
        Llamado por FastSocketServer con la queue de cada cliente conectado.

        Cada item tiene la forma ``(msg: str, addr: tuple)`` según
        ``ClientType.run()``. Se drena de forma no bloqueante para no
        detener el loop del servidor mientras espera mensajes de otros clientes.
        """
        while not queue.empty():
            try:
                msg, addr = queue.get_nowait()
            except Exception:
                break

            command = msg.strip() if msg else ""
            if not command:
                continue

            interp = self._get_or_create_session(addr)
            interp.add_command_task(command)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, block: bool = True) -> None:
        """
        Arranca el servidor.

        Parameters
        ----------
        block : bool
            Si es ``True`` (default) el metodo bloquea el hilo actual.
            Pasarlo a ``False`` es util en tests o cuando se quiere
            controlar el loop desde fuera.
        """
        Logger.print_log_normal(
            f"SandroDB server listening on {self.host}:{self.port}", "SandroServer"
        )
        self._socket_server.start()

    @property
    def active_sessions(self) -> int:
        """Numero de sesiones de cliente activas en este momento."""
        return len(self._sessions)
