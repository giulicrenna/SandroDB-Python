# -*- coding: utf-8 -*-
"""
User & Privileges CLI
======================
Interprete de linea de comandos para gestionar usuarios y privilegios.
Demuestra control de acceso en tiempo real: cada sesion respeta los
permisos del usuario autenticado.

Comandos (sin login):
  login  <user> <password>  - autenticarse
  help                      - mostrar ayuda
  exit                      - salir

Comandos (con login):
  logout                    - cerrar sesion
  whoami                    - ver usuario y privilegios actuales
  show users                - listar usuarios registrados
  show schemes              - listar schemes disponibles
  read  <scheme> <key>      - leer un registro
  write <scheme> <key> <val>- escribir un registro (requiere ADD_REGISTRY)
  mkscheme <name>           - crear un scheme (requiere ADD_SCHEME)
  help                      - mostrar ayuda
  exit                      - guardar y salir

Usuarios pre-cargados:
  root     / root        -> privilegios totales
  analyst  / analyst123  -> solo lectura
  editor   / editor456   -> lectura + escritura
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database import Database, Data
from src.user import User, UserScheme
from src.privileges import Privileges, PrivilegesScheme
from src.logger import Color
from src.exceptions import (
    KeyNotFound, NotEnoughPrivileges, InvalidSchemeName,
    InvalidPasswordException, UserDoesNotExist, SchemeAlreadyThere,
    UserPrivilegesAlreadySetted,
)

# --- Output helpers -------------------------------------------------------

def ok(msg):   print(Color.GREEN  + "[OK]  " + Color.END + msg)
def err(msg):  print(Color.RED    + "[ERR] " + Color.END + msg)
def info(msg): print(Color.CYAN   + "[INF] " + Color.END + msg)
def warn(msg): print(Color.YELLOW + "[WRN] " + Color.END + msg)

# --- Bootstrap users and privileges ---------------------------------------

def build_user_scheme() -> tuple[UserScheme, PrivilegesScheme]:
    us = UserScheme()  # already contains root:root

    analyst = User("analyst")
    analyst.set_password("analyst123")
    editor  = User("editor")
    editor.set_password("editor456")

    for u in (analyst, editor):
        try:
            us.add_user(u)
        except Exception:
            pass

    ps = PrivilegesScheme()

    root_u = us.get_user("root", "root")
    root_p = Privileges()
    root_p.make_root()

    analyst_p = Privileges()
    analyst_p.READ_SCHEME     = True
    analyst_p.GET_ALL_SCHEMES = True

    editor_p = Privileges()
    editor_p.READ_SCHEME     = True
    editor_p.GET_ALL_SCHEMES = True
    editor_p.ADD_REGISTRY    = True
    editor_p.ADD_SCHEME      = True

    for u, p in [(root_u, root_p), (analyst, analyst_p), (editor, editor_p)]:
        try:
            ps.add_privilege(user=u, privileges=p)
        except UserPrivilegesAlreadySetted:
            pass

    return us, ps

# --- CLI ------------------------------------------------------------------

class PrivilegesCLI:
    PROMPT_GUEST  = Color.YELLOW + "acl" + Color.END + "(guest) > "

    def __init__(self):
        self.user_scheme, self.priv_scheme = build_user_scheme()
        self._current_user: User | None = None
        self._db: Database | None = None

    @property
    def prompt(self) -> str:
        if self._current_user:
            return (Color.GREEN + "acl" + Color.END +
                    f"({self._current_user.name}) > ")
        return self.PROMPT_GUEST

    def _open_db(self, user: User) -> Database:
        db = Database(db_name="acl_demo", user=user)
        db.privileges_scheme = self.priv_scheme
        db.schemes_table.privileges_scheme = self.priv_scheme
        db.schemes_table.current_user_privileges = \
            self.priv_scheme.get_privileges(user=user)
        existing = db.read_all_schemes().keys()
        if "notes" not in existing:
            db.add_scheme("notes", str, str, rewrite_keys=True, scheme_size_mb=4)
            db.insert_into_scheme("notes", Data("welcome", "Hello from SandroDB!"))
            db.insert_into_scheme("notes", Data("tip", "Privileges control what you can do."))
        return db

    # --- handlers ---------------------------------------------------------

    def cmd_login(self, args: str) -> None:
        parts = args.split()
        if len(parts) != 2:
            err("Usage: login <user> <password>")
            return
        username, password = parts
        try:
            user = self.user_scheme.get_user(username, password)
            self._current_user = user
            self._db = self._open_db(user)
            privs = self.priv_scheme.get_privileges(user)
            ok(f"Logged in as '{username}'.")
            info(f"Privileges: " + " ".join(
                k for k, v in vars(privs).items() if v is True
            ))
        except (UserDoesNotExist, InvalidPasswordException):
            err("Invalid username or password.")

    def cmd_logout(self, _args: str) -> None:
        if not self._current_user:
            warn("Not logged in.")
            return
        name = self._current_user.name
        if self._db:
            self._db.close()
        self._current_user = None
        self._db = None
        ok(f"Logged out as '{name}'.")

    def cmd_whoami(self, _args: str) -> None:
        if not self._current_user:
            warn("Not logged in.")
            return
        privs = self.priv_scheme.get_privileges(self._current_user)
        active = [k for k, v in vars(privs).items() if v is True]
        print(f"\n  User      : {Color.BOLD}{self._current_user.name}{Color.END}")
        print(f"  Privileges: {', '.join(active) if active else '(none)'}\n")

    def cmd_show(self, args: str) -> None:
        if not self._current_user:
            err("Must login first.")
            return
        target = args.strip().lower()
        if target == "users":
            users = self.user_scheme.get_all_users()
            info(f"{len(users)} registered user(s):")
            for u in users:
                print(f"    - {u.name}")
        elif target == "schemes":
            try:
                schemes = self._db.read_all_schemes()
                info(f"{len(schemes)} scheme(s):")
                for name in schemes:
                    print(f"    - {name}  ({len(schemes[name])} records)")
            except NotEnoughPrivileges:
                err("Not enough privileges to list schemes.")
        else:
            err("Usage: show users | show schemes")

    def cmd_read(self, args: str) -> None:
        if not self._current_user:
            err("Must login first.")
            return
        parts = args.split(maxsplit=1)
        if len(parts) != 2:
            err("Usage: read <scheme> <key>")
            return
        scheme, key = parts
        try:
            value = self._db.get_registry(scheme, key)
            print(f"  {Color.BOLD}{key}{Color.END} = {value}")
        except NotEnoughPrivileges:
            err("Not enough privileges to read.")
        except InvalidSchemeName:
            err(f"Scheme '{scheme}' does not exist.")
        except KeyNotFound:
            err(f"Key '{key}' not found in '{scheme}'.")

    def cmd_write(self, args: str) -> None:
        if not self._current_user:
            err("Must login first.")
            return
        parts = args.split(maxsplit=2)
        if len(parts) != 3:
            err("Usage: write <scheme> <key> <value>")
            return
        scheme, key, value = parts
        try:
            self._db.insert_into_scheme(scheme, Data(key, value))
            ok(f"Written '{key}' in '{scheme}'.")
        except NotEnoughPrivileges:
            err("Not enough privileges to write.")
        except InvalidSchemeName:
            err(f"Scheme '{scheme}' does not exist.")

    def cmd_mkscheme(self, args: str) -> None:
        if not self._current_user:
            err("Must login first.")
            return
        name = args.strip()
        if not name:
            err("Usage: mkscheme <name>")
            return
        try:
            self._db.add_scheme(name, str, str, rewrite_keys=True, scheme_size_mb=2)
            ok(f"Scheme '{name}' created.")
        except NotEnoughPrivileges:
            err("Not enough privileges to create schemes.")
        except SchemeAlreadyThere:
            err(f"Scheme '{name}' already exists.")

    def cmd_help(self, _args: str) -> None:
        print(Color.BOLD + "\n  Privileges CLI — Commands\n" + Color.END)
        rows = [
            ("login  <user> <pass>",     "Authenticate"),
            ("logout",                   "End session"),
            ("whoami",                   "Show current user and privileges"),
            ("show users",               "List registered users"),
            ("show schemes",             "List available schemes"),
            ("read  <scheme> <key>",     "Read a record"),
            ("write <scheme> <key> <v>", "Write a record (ADD_REGISTRY needed)"),
            ("mkscheme <name>",          "Create a scheme (ADD_SCHEME needed)"),
            ("help",                     "Show this help"),
            ("exit",                     "Save and quit"),
        ]
        for cmd, desc in rows:
            print(f"  {Color.CYAN}{cmd:<32}{Color.END} {desc}")
        print()

    def cmd_exit(self, _args: str) -> None:
        if self._db:
            self._db.close()
        ok("Goodbye.")
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
        print(Color.BOLD + "\n  User & Privileges CLI" + Color.END +
              "  (type 'help' for commands)\n")
        info("Pre-loaded users: root/root  analyst/analyst123  editor/editor456")
        print()
        while True:
            try:
                line = input(self.prompt).strip()
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
    PrivilegesCLI().run()
