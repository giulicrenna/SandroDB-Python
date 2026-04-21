# -*- coding: utf-8 -*-
"""
serve.py — SandroDB Server entry point
========================================
Levanta el servidor de SandroDB usando FastSocket 2.0.0.

Uso
---
    # Configuracion por defecto (0.0.0.0:65432)
    python serve.py

    # Host y puerto personalizados
    python serve.py --host 192.168.1.10 --port 9000

    # Solo localhost
    python serve.py --host 127.0.0.1

Argumentos
----------
    --host   IP en la que escucha el servidor          [default: 0.0.0.0]
    --port   Puerto TCP                                [default: 65432]
    --quiet  Suprime mensajes de log informativos
"""

import argparse
import sys
import os
import time

# Asegurar que el paquete src sea encontrable desde cualquier directorio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.server import SandroServer, DEFAULT_HOST, DEFAULT_PORT
from src.logger import Logger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="serve.py",
        description="SandroDB — servidor TCP (FastSocket 2.0.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python serve.py
  python serve.py --host 0.0.0.0 --port 8080
  python serve.py --host 127.0.0.1 --quiet
        """,
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Direccion IP a escuchar (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Puerto TCP (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suprime mensajes de log informativos",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.quiet:
        Logger.print_log_normal(
            f"Starting SandroDB on {args.host}:{args.port}", "serve"
        )
        Logger.print_log_normal(
            "Press Ctrl+C to stop the server.", "serve"
        )

    server = SandroServer(host=args.host, port=args.port)
    server.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        Logger.print_log_warning("Server stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
