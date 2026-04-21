# -*- coding: utf-8 -*-
"""
Ejemplo 1 — Conexion desde terminal
======================================
Demuestra como conectarse a un servidor SandroDB en ejecucion
usando el cliente de terminal interactivo.

Prerrequisitos
--------------
  1. Tener el servidor corriendo:
         python serve.py --host localhost --port 65432

  2. Ejecutar este script en otra terminal:
         python examples/server_client/example_terminal.py

Lo que hace este script
------------------------
  - Conecta al servidor
  - Ejecuta una secuencia de comandos automaticamente
  - Imprime cada respuesta del servidor
  - Deja el control al usuario en modo REPL interactivo

Nota: requiere que el servidor este levantado ANTES de ejecutar.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.client import SandroClient
from src.logger import Color


HOST = "localhost"
PORT = 65432

# Secuencia de comandos a ejecutar automaticamente al conectar
STARTUP_COMMANDS = [
    "login root root",
    "show_databases",
    "create_db demo_terminal",
    "use_db demo_terminal",
    "create_scheme kv str str True 32",
    "insert_into kv hello world",
    "insert_into kv version 1.0",
    "get_registry kv hello",
    "show_schemes",
    "get_all_registry",
]


def main() -> None:
    print(Color.BOLD + "\n  SandroDB — Ejemplo terminal\n" + Color.END)

    client = SandroClient(host=HOST, port=PORT)
    try:
        client.connect()
        print(f"  Conectado a {HOST}:{PORT}\n")
    except Exception as exc:
        print(Color.RED + f"  No se pudo conectar: {exc}" + Color.END)
        print("  Asegurate de correr primero: python serve.py")
        sys.exit(1)

    # -- Ejecutar secuencia inicial ----------------------------------------
    print(Color.CYAN + "  [auto] Ejecutando secuencia de inicio...\n" + Color.END)
    for cmd in STARTUP_COMMANDS:
        print(Color.YELLOW + f"  > {cmd}" + Color.END)
        response = client.send_command(cmd)
        print(f"  {response}\n")

    # -- REPL interactivo --------------------------------------------------
    print(Color.BOLD + "  Modo interactivo. Escribe 'exit' para salir.\n" + Color.END)
    prompt = Color.GREEN + "sandro" + Color.END + " > "

    while True:
        try:
            line = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not line:
            continue
        if line.lower() in ("exit", "quit"):
            break

        response = client.send_command(line)
        print(response)

    client.disconnect()
    print("\n  Desconectado.")


if __name__ == "__main__":
    main()
