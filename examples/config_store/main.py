# -*- coding: utf-8 -*-
"""
Config Store CLI
=================
Interprete de linea de comandos para gestionar configuracion de aplicacion.

Schemes:
  - app_config : str -> str  (rewrite=True,  valores mutables)
  - secrets    : str -> str  (rewrite=False, escritura unica)

Comandos:
  get    <key>             - leer un valor de app_config
  set    <key> <value>     - escribir/actualizar en app_config
  secret get <key>         - leer un secret (valor enmascarado)
  secret set <key> <value> - escribir un secret (write-once)
  list   [secrets]         - listar todas las claves (o secrets)
  delete <key>             - borrar key de app_config creando scheme nuevo
  help                     - mostrar ayuda
  exit                     - guardar y salir
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import Database, Data
from src.user import User
from src.logger import Color
from src.exceptions import KeyNotFound, SchemeReachedMaxSize

# --- Output helpers -------------------------------------------------------

def ok(msg):   print(Color.GREEN  + "[OK]  " + Color.END + msg)
def err(msg):  print(Color.RED    + "[ERR] " + Color.END + msg)
def info(msg): print(Color.CYAN   + "[INF] " + Color.END + msg)
def warn(msg): print(Color.YELLOW + "[WRN] " + Color.END + msg)

def mask(value: str) -> str:
    if len(value) <= 4:
        return "*" * len(value)
    return value[:2] + "*" * (len(value) - 4) + value[-2:]

# --- CLI ------------------------------------------------------------------

class ConfigCLI:
    PROMPT = Color.BLUE + "config" + Color.END + " > "

    def __init__(self):
        root = User("root")
        root.set_password("root")
        self.db = Database(db_name="app_config", user=root)

        existing = self.db.read_all_schemes().keys()
        if "app_config" not in existing:
            self.db.add_scheme("app_config", str, str,
                               rewrite_keys=True, scheme_size_mb=2)
        if "secrets" not in existing:
            self.db.add_scheme("secrets", str, str,
                               rewrite_keys=False, scheme_size_mb=1)

    # --- helpers ----------------------------------------------------------

    def _config(self) -> dict:
        return self.db.read_all_schemes().get("app_config", {})

    def _secrets(self) -> dict:
        return self.db.read_all_schemes().get("secrets", {})

    # --- handlers ---------------------------------------------------------

    def cmd_get(self, args: str) -> None:
        key = args.strip()
        if not key:
            err("Usage: get <key>")
            return
        try:
            value = self.db.get_registry("app_config", key)
            print(f"  {Color.BOLD}{key}{Color.END} = {value}")
        except KeyNotFound:
            err(f"Key '{key}' not found in app_config.")

    def cmd_set(self, args: str) -> None:
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            err("Usage: set <key> <value>")
            return
        key, value = parts
        try:
            self.db.insert_into_scheme("app_config", Data(key, value))
            ok(f"'{key}' = '{value}'")
        except SchemeReachedMaxSize:
            err("app_config scheme is full.")

    def cmd_secret(self, args: str) -> None:
        parts = args.split(maxsplit=2)
        if len(parts) < 2:
            err("Usage: secret get <key>  |  secret set <key> <value>")
            return
        subcommand = parts[0].lower()
        if subcommand == "get":
            key = parts[1]
            try:
                value = self.db.get_registry("secrets", key)
                print(f"  {Color.BOLD}{key}{Color.END} = {mask(value)}")
            except KeyNotFound:
                err(f"Secret '{key}' not found.")
        elif subcommand == "set":
            if len(parts) < 3:
                err("Usage: secret set <key> <value>")
                return
            key, value = parts[1], parts[2]
            before = self._secrets().get(key)
            self.db.insert_into_scheme("secrets", Data(key, value))
            after = self._secrets().get(key)
            if before is not None and after == before:
                warn(f"'{key}' already exists — write-once scheme, value NOT changed.")
            else:
                ok(f"Secret '{key}' stored.")
        else:
            err("Usage: secret get <key>  |  secret set <key> <value>")

    def cmd_list(self, args: str) -> None:
        if args.strip() == "secrets":
            data = self._secrets()
            label = "secrets"
        else:
            data = self._config()
            label = "app_config"
        if not data:
            warn(f"No entries in {label}.")
            return
        info(f"{len(data)} key(s) in {label}:")
        for key, value in data.items():
            display = mask(value) if label == "secrets" else value
            print(f"  {Color.CYAN}{key:<24}{Color.END} = {display}")

    def cmd_help(self, _args: str) -> None:
        print(Color.BOLD + "\n  Config Store CLI — Commands\n" + Color.END)
        rows = [
            ("get    <key>",              "Read a config value"),
            ("set    <key> <value>",      "Write/overwrite a config value"),
            ("secret get <key>",          "Read a secret (masked)"),
            ("secret set <key> <value>",  "Write a secret (write-once)"),
            ("list",                      "List all config keys"),
            ("list   secrets",            "List all secret keys (masked)"),
            ("help",                      "Show this help"),
            ("exit",                      "Save and quit"),
        ]
        for cmd, desc in rows:
            print(f"  {Color.CYAN}{cmd:<32}{Color.END} {desc}")
        print()

    def cmd_exit(self, _args: str) -> None:
        self.db.close()
        ok("Config saved. Goodbye.")
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
            err(f"Unknown command '{cmd}'. Type 'help'.")

    def run(self) -> None:
        print(Color.BOLD + "\n  Config Store CLI" + Color.END +
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
    ConfigCLI().run()
