# -*- coding: utf-8 -*-
"""
Inventory CLI
==============
Interprete de linea de comandos para gestionar un inventario de productos.

Schemes:
  - products : str -> str  (id -> descripcion)
  - prices   : str -> str  (id -> precio)
  - stock    : str -> str  (id -> cantidad)

Comandos:
  list                      - listar todos los productos
  get   <id>                - ver detalle de un producto
  add   <id> <precio> <desc>- agregar o actualizar producto
  stock <id> <cantidad>     - actualizar stock
  search <texto>            - buscar en descripciones
  help                      - mostrar ayuda
  exit                      - guardar y salir
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import Database, Data
from src.user import User
from src.logger import Color
from src.exceptions import KeyNotFound, SchemeAlreadyThere

# --- Output helpers -------------------------------------------------------

def ok(msg: str)    -> None: print(Color.GREEN  + "[OK]  " + Color.END + msg)
def err(msg: str)   -> None: print(Color.RED    + "[ERR] " + Color.END + msg)
def info(msg: str)  -> None: print(Color.CYAN   + "[INF] " + Color.END + msg)
def warn(msg: str)  -> None: print(Color.YELLOW + "[WRN] " + Color.END + msg)

def print_row(pid, desc, price, qty):
    print(f"  {Color.BOLD}{pid:<8}{Color.END} {desc:<28} ${float(price):>8.2f}   qty: {qty}")

# --- CLI class ------------------------------------------------------------

class InventoryCLI:
    PROMPT = Color.BLUE + "inventory" + Color.END + " > "

    def __init__(self):
        root = User("root")
        root.set_password("root")
        self.db = Database(db_name="inventory", user=root)

        existing = self.db.read_all_schemes().keys()
        for scheme, size in [("products", 16), ("prices", 8), ("stock", 8)]:
            if scheme not in existing:
                self.db.add_scheme(scheme, str, str, rewrite_keys=True, scheme_size_mb=size)

    # --- command handlers -------------------------------------------------

    def cmd_list(self, _args: str) -> None:
        all_schemes = self.db.read_all_schemes()
        products = all_schemes.get("products", {})
        if not products:
            warn("No products found.")
            return
        print(f"\n  {'ID':<8} {'DESCRIPTION':<28} {'PRICE':>10}   STOCK")
        print("  " + "-" * 58)
        for pid, desc in products.items():
            price = all_schemes.get("prices", {}).get(pid, "0.00")
            qty   = all_schemes.get("stock",  {}).get(pid, "0")
            print_row(pid, desc, price, qty)
        print()

    def cmd_get(self, args: str) -> None:
        pid = args.strip()
        if not pid:
            err("Usage: get <id>")
            return
        try:
            desc  = self.db.get_registry("products", pid)
            price = self.db.get_registry("prices",   pid)
            qty   = self.db.get_registry("stock",    pid)
            print(f"\n  ID      : {Color.BOLD}{pid}{Color.END}")
            print(f"  Desc    : {desc}")
            print(f"  Price   : ${float(price):.2f}")
            print(f"  Stock   : {qty} units\n")
        except KeyNotFound:
            err(f"Product '{pid}' not found.")

    def cmd_add(self, args: str) -> None:
        parts = args.split(maxsplit=2)
        if len(parts) < 3:
            err("Usage: add <id> <price> <description>")
            return
        pid, price, desc = parts[0], parts[1], parts[2]
        try:
            float(price)
        except ValueError:
            err(f"'{price}' is not a valid price.")
            return
        self.db.insert_into_scheme("products", Data(pid, desc))
        self.db.insert_into_scheme("prices",   Data(pid, price))
        self.db.insert_into_scheme("stock",    Data(pid, "0"))
        ok(f"Product '{pid}' saved.")

    def cmd_stock(self, args: str) -> None:
        parts = args.split()
        if len(parts) != 2:
            err("Usage: stock <id> <cantidad>")
            return
        pid, qty = parts[0], parts[1]
        if not qty.isdigit():
            err(f"'{qty}' is not a valid integer.")
            return
        try:
            self.db.get_registry("products", pid)
        except KeyNotFound:
            err(f"Product '{pid}' does not exist. Use 'add' first.")
            return
        self.db.insert_into_scheme("stock", Data(pid, qty))
        ok(f"Stock for '{pid}' updated to {qty}.")

    def cmd_search(self, args: str) -> None:
        query = args.strip().lower()
        if not query:
            err("Usage: search <text>")
            return
        products = self.db.read_all_schemes().get("products", {})
        results  = {pid: desc for pid, desc in products.items() if query in desc.lower()}
        if not results:
            warn(f"No products matching '{query}'.")
            return
        info(f"{len(results)} result(s) for '{query}':")
        prices = self.db.read_all_schemes().get("prices", {})
        stock  = self.db.read_all_schemes().get("stock",  {})
        for pid, desc in results.items():
            print_row(pid, desc, prices.get(pid, "0"), stock.get(pid, "0"))

    def cmd_help(self, _args: str) -> None:
        print(Color.BOLD + "\n  Inventory CLI — Commands\n" + Color.END)
        cmds = [
            ("list",                   "List all products"),
            ("get   <id>",             "Show product detail"),
            ("add   <id> <price> <desc>","Add or update a product"),
            ("stock <id> <qty>",       "Update stock quantity"),
            ("search <text>",          "Search products by description"),
            ("help",                   "Show this help"),
            ("exit",                   "Save and quit"),
        ]
        for cmd, desc in cmds:
            print(f"  {Color.CYAN}{cmd:<30}{Color.END} {desc}")
        print()

    def cmd_exit(self, _args: str) -> None:
        self.db.close()
        ok("Database saved. Goodbye.")
        sys.exit(0)

    # --- dispatch + run ---------------------------------------------------

    def dispatch(self, line: str) -> None:
        parts = line.strip().split(maxsplit=1)
        cmd   = parts[0].lower()
        args  = parts[1] if len(parts) > 1 else ""
        handler = getattr(self, f"cmd_{cmd}", None)
        if handler:
            handler(args)
        else:
            err(f"Unknown command '{cmd}'. Type 'help' for a list.")

    def run(self) -> None:
        print(Color.BOLD + "\n  Inventory CLI" + Color.END +
              "  (type 'help' for commands)\n")
        while True:
            try:
                line = input(self.PROMPT).strip()
                if not line:
                    continue
                self.dispatch(line)
            except KeyboardInterrupt:
                print()
                self.cmd_exit("")
            except EOFError:
                self.cmd_exit("")

# --- Entry point ----------------------------------------------------------

if __name__ == "__main__":
    InventoryCLI().run()
