# -*- coding: utf-8 -*-
"""
Pokedex CLI
============
Interprete de linea de comandos para explorar datos de Pokemon.
Los datos se obtienen de PokeAPI (https://pokeapi.co) y se cachean
en SandroDB. Las busquedas posteriores no requieren conexion.

API: https://pokeapi.co/api/v2/pokemon/{name}  (gratuita, sin key)

Schemes:
  - stats  : str -> str  (nombre -> "hp/atk/def/spa/spd/spe")
  - types  : str -> str  (nombre -> "tipo1[/tipo2]")
  - moves  : str -> str  (nombre -> primer movimiento)
  - height : str -> str  (nombre -> altura en dm)

Comandos:
  fetch  <nombre>    - descargar Pokemon desde la API y guardarlo
  info   <nombre>    - ver detalle de un Pokemon (usa cache)
  list               - listar todos los Pokemon en la DB
  type   <tipo>      - filtrar por tipo (ej: fire, water, psychic)
  top    <stat>      - top 5 por stat (hp/atk/def/spa/spd/spe)
  help               - mostrar ayuda
  exit               - guardar y salir
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import urllib.request
import urllib.error
import json

from src.database import Database, Data
from src.user import User
from src.logger import Color
from src.exceptions import KeyNotFound

# --- API layer -----------------------------------------------------------

API_BASE = "https://pokeapi.co/api/v2/pokemon"

STAT_LABELS = ["hp", "atk", "def", "spa", "spd", "spe"]
STAT_KEYS   = ["hp", "attack", "defense", "special-attack", "special-defense", "speed"]

def _fetch_raw(name: str) -> dict | None:
    try:
        url = f"{API_BASE}/{name.lower()}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except urllib.error.URLError as e:
        raise ConnectionError(str(e))

def parse_pokemon(data: dict) -> dict:
    stat_map = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    return {
        "stats":  "/".join(str(stat_map.get(k, 0)) for k in STAT_KEYS),
        "types":  "/".join(t["type"]["name"] for t in data["types"]),
        "moves":  data["moves"][0]["move"]["name"] if data.get("moves") else "none",
        "height": str(data["height"]),
    }

# --- Output helpers -------------------------------------------------------

def ok(msg):   print(Color.GREEN  + "[OK]  " + Color.END + msg)
def err(msg):  print(Color.RED    + "[ERR] " + Color.END + msg)
def info(msg): print(Color.CYAN   + "[INF] " + Color.END + msg)
def warn(msg): print(Color.YELLOW + "[WRN] " + Color.END + msg)

def _stat_bar(value: int, max_val: int = 255, width: int = 20) -> str:
    filled = int(value / max_val * width)
    return Color.GREEN + "#" * filled + Color.END + "-" * (width - filled)

# --- CLI ------------------------------------------------------------------

class PokedexCLI:
    PROMPT = Color.RED + "pokedex" + Color.END + " > "

    def __init__(self):
        root = User("root")
        root.set_password("root")
        self.db = Database(db_name="pokedex", user=root)

        existing = self.db.read_all_schemes().keys()
        for scheme in ("stats", "types", "moves", "height"):
            if scheme not in existing:
                self.db.add_scheme(scheme, str, str,
                                   rewrite_keys=True, scheme_size_mb=8)

    # --- handlers ---------------------------------------------------------

    def cmd_fetch(self, args: str) -> None:
        name = args.strip().lower()
        if not name:
            err("Usage: fetch <nombre>")
            return
        info(f"Fetching '{name}' from PokeAPI...")
        try:
            raw = _fetch_raw(name)
        except ConnectionError as e:
            err(f"Network error: {e}")
            return
        if raw is None:
            err(f"Pokemon '{name}' not found in PokeAPI.")
            return
        parsed = parse_pokemon(raw)
        for scheme, value in parsed.items():
            self.db.insert_into_scheme(scheme, Data(name, value))
        ok(f"'{name}' stored.  types={parsed['types']}  "
           f"stats={parsed['stats']}")

    def cmd_info(self, args: str) -> None:
        name = args.strip().lower()
        if not name:
            err("Usage: info <nombre>")
            return
        try:
            stats_str = self.db.get_registry("stats",  name)
            types_str = self.db.get_registry("types",  name)
            move      = self.db.get_registry("moves",  name)
            height_dm = int(self.db.get_registry("height", name))
        except KeyNotFound:
            err(f"'{name}' not in DB. Use 'fetch {name}' first.")
            return

        stat_vals = [int(v) for v in stats_str.split("/")]

        print(f"\n  {Color.BOLD}{name.upper()}{Color.END}")
        print(f"  Type     : {types_str}")
        print(f"  Height   : {height_dm / 10:.1f} m")
        print(f"  Signature: {move}")
        print(f"\n  {'STAT':<6} {'VAL':>4}  BAR")
        print("  " + "-" * 36)
        for label, val in zip(STAT_LABELS, stat_vals):
            bar = _stat_bar(val)
            print(f"  {label.upper():<6} {val:>4}  {bar}")
        print()

    def cmd_list(self, _args: str) -> None:
        all_stats = self.db.read_all_schemes().get("stats", {})
        if not all_stats:
            warn("No Pokemon in DB. Use 'fetch <name>' to add some.")
            return
        print(f"\n  {'NAME':<14} {'TYPE':<18} {'HP/ATK/DEF/SpA/SpD/SPE'}")
        print("  " + "-" * 60)
        for name, stats in all_stats.items():
            ptype = self.db.read_all_schemes().get("types", {}).get(name, "?")
            print(f"  {name:<14} {ptype:<18} {stats}")
        print(f"\n  {len(all_stats)} Pokemon cached.\n")

    def cmd_type(self, args: str) -> None:
        target = args.strip().lower()
        if not target:
            err("Usage: type <tipo>  (ej: fire, water, psychic)")
            return
        types_data = self.db.read_all_schemes().get("types", {})
        results = [n for n, t in types_data.items() if target in t.split("/")]
        if not results:
            warn(f"No Pokemon of type '{target}' in DB.")
            return
        info(f"{len(results)} {target}-type Pokemon:")
        for name in results:
            t = types_data[name]
            print(f"    {Color.CYAN}{name:<14}{Color.END} ({t})")

    def cmd_top(self, args: str) -> None:
        stat = args.strip().lower()
        if stat not in STAT_LABELS:
            err(f"Valid stats: {', '.join(STAT_LABELS)}")
            return
        idx = STAT_LABELS.index(stat)
        all_stats = self.db.read_all_schemes().get("stats", {})
        if not all_stats:
            warn("No Pokemon in DB.")
            return
        ranked = sorted(
            ((name, int(s.split("/")[idx])) for name, s in all_stats.items()),
            key=lambda x: x[1], reverse=True
        )[:5]
        info(f"Top {len(ranked)} by {stat.upper()}:")
        for i, (name, val) in enumerate(ranked, 1):
            bar = _stat_bar(val)
            print(f"  {i}. {name:<14} {val:>4}  {bar}")
        print()

    def cmd_help(self, _args: str) -> None:
        print(Color.BOLD + "\n  Pokedex CLI — Commands\n" + Color.END)
        rows = [
            ("fetch  <nombre>",  "Descargar Pokemon desde PokeAPI"),
            ("info   <nombre>",  "Ver detalle con barra de stats"),
            ("list",             "Listar todos los Pokemon en DB"),
            ("type   <tipo>",    "Filtrar por tipo (fire, water...)"),
            ("top    <stat>",    "Top 5 por stat (hp/atk/def/spa/spd/spe)"),
            ("help",             "Mostrar esta ayuda"),
            ("exit",             "Guardar y salir"),
        ]
        for cmd, desc in rows:
            print(f"  {Color.CYAN}{cmd:<22}{Color.END} {desc}")
        print()

    def cmd_exit(self, _args: str) -> None:
        self.db.close()
        ok("Pokedex saved. Goodbye.")
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
        print(Color.BOLD + "\n  Pokedex CLI" + Color.END +
              "  (type 'help' for commands)\n")
        cached = len(self.db.read_all_schemes().get("stats", {}))
        if cached:
            info(f"{cached} Pokemon already cached in DB.")
        else:
            info("DB empty. Try: fetch pikachu")
        print()
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
    PokedexCLI().run()
