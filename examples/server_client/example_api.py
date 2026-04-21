# -*- coding: utf-8 -*-
"""
Ejemplo 2 — Uso programatico desde codigo Python
==================================================
Demuestra el uso de ``SandroClient`` como libreria dentro de codigo
Python, sin necesidad de intervencion del usuario.

Prerrequisitos
--------------
  1. Tener el servidor corriendo:
         python serve.py

  2. Ejecutar este script:
         python examples/server_client/example_api.py

Caso de uso simulado
---------------------
  Un sistema de e-commerce que registra productos y ordenes
  en SandroDB via red, usando la API tipada de SandroClient.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.client import SandroClient


HOST = "localhost"
PORT = 65432


# ---------------------------------------------------------------------------
# Datos del ejemplo
# ---------------------------------------------------------------------------

PRODUCTS = {
    "P001": "Mechanical Keyboard RGB",
    "P002": "4K Webcam",
    "P003": "USB-C Docking Station",
}

PRICES = {
    "P001": "89.99",
    "P002": "129.00",
    "P003": "59.50",
}

ORDERS = {
    "ORD-001": "P001",
    "ORD-002": "P003",
    "ORD-003": "P002",
}


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def log(label: str, response: str) -> None:
    status = "OK" if "ERROR" not in response and "TIMEOUT" not in response else "!!"
    print(f"  [{status}] {label:<35} {response.strip()[:60]}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n  SandroDB — Ejemplo API programatica\n")

    client = SandroClient(host=HOST, port=PORT, timeout=8.0)

    try:
        client.connect()
        print(f"  Conectado a {HOST}:{PORT}\n")
    except Exception as exc:
        print(f"  Error de conexion: {exc}")
        print("  Asegurate de correr primero: python serve.py")
        sys.exit(1)

    # -- Autenticacion -----------------------------------------------------
    print("  === Autenticacion ===")
    log("login root", client.login("root", "root"))

    # -- Crear base de datos -----------------------------------------------
    print("\n  === Crear base de datos ===")
    log("create_db ecommerce", client.create_db("ecommerce"))
    log("use_db ecommerce",    client.use_db("ecommerce"))

    # -- Crear schemes -------------------------------------------------------
    print("\n  === Crear schemes ===")
    log("create_scheme products", client.create_scheme("products", "str", "str", overwrite=True,  size_mb=32))
    log("create_scheme prices",   client.create_scheme("prices",   "str", "str", overwrite=True,  size_mb=16))
    log("create_scheme orders",   client.create_scheme("orders",   "str", "str", overwrite=False, size_mb=64))
    log("show_schemes",           client.show_schemes())

    # -- Insertar productos --------------------------------------------------
    print("\n  === Insertar productos ===")
    for pid, desc in PRODUCTS.items():
        log(f"insert product {pid}", client.insert("products", pid, desc))
    for pid, price in PRICES.items():
        log(f"insert price {pid}",   client.insert("prices", pid, price))

    # -- Registrar ordenes (write-once) --------------------------------------
    print("\n  === Registrar ordenes (write-once) ===")
    for oid, pid in ORDERS.items():
        log(f"insert order {oid}", client.insert("orders", oid, pid))

    # -- Intentar sobreescribir orden (debe fallar silenciosamente) ----------
    log("re-insert ORD-001 (ignored)", client.insert("orders", "ORD-001", "P999"))

    # -- Consultas ------------------------------------------------------------
    print("\n  === Consultas ===")
    log("get product P002",  client.get("products", "P002"))
    log("get price P003",    client.get("prices",   "P003"))
    log("get order ORD-002", client.get("orders",   "ORD-002"))

    # -- Dump completo --------------------------------------------------------
    print("\n  === Todos los schemes ===")
    log("get_all_registry", client.get_all())

    # -- Fin ------------------------------------------------------------------
    client.disconnect()
    print("\n  Desconectado. DB persistida en el servidor.")


if __name__ == "__main__":
    main()
