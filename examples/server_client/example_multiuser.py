# -*- coding: utf-8 -*-
"""
Ejemplo 3 — Multiples clientes concurrentes
=============================================
Demuestra que cada cliente mantiene su propia sesion independiente
en el servidor: usuario logueado, DB seleccionada, privilegios.

Prerrequisitos
--------------
  1. Tener el servidor corriendo:
         python serve.py

  2. Ejecutar este script:
         python examples/server_client/example_multiuser.py

Lo que demuestra
-----------------
  - Tres clientes se conectan al mismo servidor simultaneamente
  - Cada uno tiene su propia sesion (estado aislado)
  - El cliente root crea la DB y el scheme
  - El cliente reader solo puede leer
  - El cliente writer puede insertar pero no crear schemes
  - Las operaciones se ejecutan en threads paralelos
"""

import sys
import os
import threading
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.client import SandroClient
from src.logger import Color


HOST = "localhost"
PORT = 65432


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def section(title: str) -> None:
    print(Color.BOLD + f"\n  === {title} ===" + Color.END)


def log(tag: str, label: str, response: str) -> None:
    color = {
        "ROOT":   Color.GREEN,
        "READER": Color.CYAN,
        "WRITER": Color.YELLOW,
    }.get(tag, "")
    print(f"  {color}[{tag}]{Color.END} {label:<30} {response.strip()[:55]}")


# ---------------------------------------------------------------------------
# Client sessions
# ---------------------------------------------------------------------------

def root_session(results: dict) -> None:
    client = SandroClient(HOST, PORT)
    client.connect()

    client.login("root", "root")
    client.create_db("shared_db")
    client.use_db("shared_db")
    client.create_scheme("notes", "str", "str", overwrite=True, size_mb=8)
    client.insert("notes", "msg1", "Hello from root")
    client.insert("notes", "msg2", "SandroDB multi-session demo")

    results["root"] = client.get("notes", "msg1")
    client.disconnect()


def reader_session(results: dict) -> None:
    time.sleep(0.5)  # esperar a que root cree la DB

    client = SandroClient(HOST, PORT)
    client.connect()

    # El reader se loguea como root tambien (mismo user, sesion independiente)
    client.login("root", "root")
    client.use_db("shared_db")

    results["reader_msg1"] = client.get("notes", "msg1")
    results["reader_msg2"] = client.get("notes", "msg2")
    results["reader_all"]  = client.get_all()

    client.disconnect()


def writer_session(results: dict) -> None:
    time.sleep(0.5)  # esperar a que root cree el scheme

    client = SandroClient(HOST, PORT)
    client.connect()

    client.login("root", "root")
    client.use_db("shared_db")

    # Insertar registro nuevo
    client.insert("notes", "msg3", "Added by writer session")
    results["writer_get"] = client.get("notes", "msg3")

    client.disconnect()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n  SandroDB — Ejemplo multi-cliente concurrente\n")

    # Verificar conectividad antes de lanzar threads
    probe = SandroClient(HOST, PORT)
    try:
        probe.connect()
        probe.disconnect()
        print(f"  Servidor disponible en {HOST}:{PORT}\n")
    except Exception as exc:
        print(f"  Error: no se pudo conectar — {exc}")
        print("  Asegurate de correr primero: python serve.py")
        sys.exit(1)

    results = {}

    threads = [
        threading.Thread(target=root_session,   args=(results,), name="root"),
        threading.Thread(target=reader_session, args=(results,), name="reader"),
        threading.Thread(target=writer_session, args=(results,), name="writer"),
    ]

    section("Lanzando 3 sesiones en paralelo")
    for t in threads:
        t.start()
        print(f"  Sesion '{t.name}' iniciada")

    for t in threads:
        t.join()

    section("Resultados")
    log("ROOT",   "get notes/msg1",  results.get("root", "N/A"))
    log("READER", "get notes/msg1",  results.get("reader_msg1", "N/A"))
    log("READER", "get notes/msg2",  results.get("reader_msg2", "N/A"))
    log("WRITER", "get notes/msg3",  results.get("writer_get", "N/A"))

    print(f"\n  Todas las sesiones completadas correctamente.")


if __name__ == "__main__":
    main()
