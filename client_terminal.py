# -*- coding: utf-8 -*-
"""
client_terminal.py — SandroDB terminal client
===============================================
Cliente interactivo de linea de comandos que se conecta a un servidor
SandroDB corriendo via ``serve.py``.

Uso
---
    # Conectar al servidor local con config por defecto
    python client_terminal.py

    # Servidor remoto
    python client_terminal.py --host 192.168.1.10 --port 9000

    # Ejecutar un unico comando y salir (modo no interactivo)
    python client_terminal.py --exec "login root root"

Argumentos
----------
    --host   Host del servidor SandroDB     [default: localhost]
    --port   Puerto TCP                     [default: 65432]
    --exec   Ejecutar comando y salir
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client import SandroClient, DEFAULT_HOST, DEFAULT_PORT
from src.logger import Color


# ---------------------------------------------------------------------------
# Helpers de output
# ---------------------------------------------------------------------------

def _banner(host: str, port: int) -> None:
    print(Color.BOLD + "\n  SandroDB Terminal Client" + Color.END)
    print(f"  Connected to {Color.CYAN}{host}:{port}{Color.END}")
    print("  Type " + Color.YELLOW + "help" + Color.END +
          " for commands, " + Color.YELLOW + "exit" + Color.END + " to quit.\n")


def _print_response(response: str) -> None:
    if response.startswith("[ERROR]") or response.startswith("[ERR]"):
        print(Color.RED + response + Color.END)
    elif response.startswith("[WARNING]"):
        print(Color.YELLOW + response + Color.END)
    elif response.startswith("[TIMEOUT]"):
        print(Color.YELLOW + response + Color.END)
    else:
        print(response)


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

PROMPT = Color.GREEN + "sandro" + Color.END + " > "

LOCAL_COMMANDS = {
    "exit", "quit",
    "clear", "cls",
}


def run_repl(client: SandroClient) -> None:
    """Bucle principal del interprete interactivo."""
    while True:
        try:
            line = input(PROMPT).strip()
        except (KeyboardInterrupt, EOFError):
            print()
            _disconnect(client)

        if not line:
            continue

        cmd = line.split()[0].lower()

        if cmd in ("exit", "quit"):
            _disconnect(client)

        if cmd in ("clear", "cls"):
            os.system("cls" if os.name == "nt" else "clear")
            continue

        response = client.send_command(line)
        _print_response(response)


def _disconnect(client: SandroClient) -> None:
    client.disconnect()
    print(Color.YELLOW + "\nDisconnected. Goodbye." + Color.END)
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="client_terminal.py",
        description="SandroDB — cliente de terminal interactivo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python client_terminal.py
  python client_terminal.py --host 192.168.1.10 --port 9000
  python client_terminal.py --exec "login root root"
        """,
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Host del servidor (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto TCP (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--exec",
        metavar="CMD",
        default=None,
        help="Ejecutar un unico comando y salir (modo no interactivo)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    client = SandroClient(host=args.host, port=args.port)

    try:
        client.connect()
    except Exception as exc:
        print(Color.RED + f"[ERROR] Could not connect to {args.host}:{args.port} — {exc}" + Color.END)
        sys.exit(1)

    if args.exec:
        # Modo no interactivo: ejecutar comando y salir
        response = client.send_command(args.exec)
        _print_response(response)
        client.disconnect()
        sys.exit(0)

    _banner(args.host, args.port)
    run_repl(client)


if __name__ == "__main__":
    main()
