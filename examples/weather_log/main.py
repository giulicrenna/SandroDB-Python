# -*- coding: utf-8 -*-
"""
Weather CLI
============
Interprete de linea de comandos para consultar y registrar datos
meteorologicos usando Open-Meteo (https://open-meteo.com).
Los datos se cachean en SandroDB y se pueden refrescar manualmente.

APIs (gratuitas, sin key):
  - Geocoding : https://geocoding-api.open-meteo.com/v1/search
  - Forecast  : https://api.open-meteo.com/v1/forecast

Schemes:
  - temperature : str -> str  (ciudad -> temperatura en C)
  - condition   : str -> str  (ciudad -> descripcion del clima)
  - humidity    : str -> str  (ciudad -> humedad %)
  - wind        : str -> str  (ciudad -> viento km/h)

Comandos:
  fetch  <ciudad>    - descargar clima actual de la ciudad
  show   [ciudad]    - mostrar tabla completa o ciudad puntual
  update <ciudad>    - refrescar datos desde la API
  stats              - promedio, ciudad mas caliente y mas fria
  help               - mostrar ayuda
  exit               - guardar y salir
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import urllib.request
import urllib.parse
import urllib.error
import json

from src.database import Database, Data
from src.user import User
from src.logger import Color
from src.exceptions import KeyNotFound

# --- WMO code map --------------------------------------------------------

WMO = {
    0: "Clear sky",       1: "Mainly clear",    2: "Partly cloudy",
    3: "Overcast",        45: "Fog",             48: "Icy fog",
    51: "Light drizzle",  53: "Drizzle",         55: "Heavy drizzle",
    61: "Light rain",     63: "Rain",            65: "Heavy rain",
    71: "Light snow",     73: "Snow",            75: "Heavy snow",
    80: "Rain showers",   81: "Showers",         82: "Violent showers",
    95: "Thunderstorm",   96: "Thunderstorm+hail", 99: "Heavy thunderstorm",
}

GEO_URL  = "https://geocoding-api.open-meteo.com/v1/search"
WTHR_URL = "https://api.open-meteo.com/v1/forecast"

# --- API layer -----------------------------------------------------------

def _get(url: str) -> dict | None:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        raise ConnectionError(str(e))

def geocode(city: str) -> tuple[float, float] | None:
    params = urllib.parse.urlencode({"name": city, "count": 1, "language": "en"})
    data = _get(f"{GEO_URL}?{params}")
    if not data or not data.get("results"):
        return None
    r = data["results"][0]
    return r["latitude"], r["longitude"]

def fetch_current(lat: float, lon: float) -> dict:
    params = urllib.parse.urlencode({
        "latitude":        lat,
        "longitude":       lon,
        "current":         "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
        "wind_speed_unit": "kmh",
        "timezone":        "auto",
    })
    data = _get(f"{WTHR_URL}?{params}")
    cur  = data["current"]
    return {
        "temp": str(cur["temperature_2m"]),
        "hum":  str(cur["relative_humidity_2m"]),
        "wind": str(cur["wind_speed_10m"]),
        "cond": WMO.get(cur["weather_code"], f"code {cur['weather_code']}"),
    }

# --- Output helpers -------------------------------------------------------

def ok(msg):   print(Color.GREEN  + "[OK]  " + Color.END + msg)
def err(msg):  print(Color.RED    + "[ERR] " + Color.END + msg)
def info(msg): print(Color.CYAN   + "[INF] " + Color.END + msg)
def warn(msg): print(Color.YELLOW + "[WRN] " + Color.END + msg)

def _temp_color(temp: float) -> str:
    if temp >= 30:
        return Color.RED
    if temp <= 5:
        return Color.BLUE
    return Color.GREEN

def _print_city_row(city: str, temp: str, hum: str, wind: str, cond: str) -> None:
    tc = _temp_color(float(temp))
    print(f"  {city:<18} {tc}{temp:>6}C{Color.END}   {hum:>4}%  "
          f"{wind:>6} km/h  {cond}")

# --- CLI ------------------------------------------------------------------

class WeatherCLI:
    PROMPT = Color.BLUE + "weather" + Color.END + " > "

    def __init__(self):
        root = User("root")
        root.set_password("root")
        self.db = Database(db_name="weather_log", user=root)

        existing = self.db.read_all_schemes().keys()
        for scheme in ("temperature", "condition", "humidity", "wind"):
            if scheme not in existing:
                self.db.add_scheme(scheme, str, str,
                                   rewrite_keys=True, scheme_size_mb=4)

    def _store(self, city: str, w: dict) -> None:
        self.db.insert_into_scheme("temperature", Data(city, w["temp"]))
        self.db.insert_into_scheme("condition",   Data(city, w["cond"]))
        self.db.insert_into_scheme("humidity",    Data(city, w["hum"]))
        self.db.insert_into_scheme("wind",        Data(city, w["wind"]))

    # --- handlers ---------------------------------------------------------

    def cmd_fetch(self, args: str) -> None:
        city = args.strip()
        if not city:
            err("Usage: fetch <ciudad>")
            return
        info(f"Fetching weather for '{city}'...")
        try:
            coords = geocode(city)
        except ConnectionError as e:
            err(f"Network error: {e}")
            return
        if coords is None:
            err(f"Could not geocode '{city}'. Check spelling.")
            return
        try:
            w = fetch_current(*coords)
        except ConnectionError as e:
            err(f"Network error: {e}")
            return
        self._store(city, w)
        ok(f"{city}: {w['temp']}C  {w['hum']}%  {w['wind']} km/h  {w['cond']}")

    def cmd_update(self, args: str) -> None:
        city = args.strip()
        if not city:
            err("Usage: update <ciudad>")
            return
        try:
            self.db.get_registry("temperature", city)
        except KeyNotFound:
            err(f"'{city}' not in DB. Use 'fetch {city}' first.")
            return
        self.cmd_fetch(city)

    def cmd_show(self, args: str) -> None:
        city = args.strip()
        temps = self.db.read_all_schemes().get("temperature", {})

        if city:
            if city not in temps:
                err(f"'{city}' not in DB. Use 'fetch {city}'.")
                return
            cond = self.db.get_registry("condition", city)
            hum  = self.db.get_registry("humidity",  city)
            wind = self.db.get_registry("wind",      city)
            temp = temps[city]
            print(f"\n  {Color.BOLD}{city}{Color.END}")
            print(f"  Temperature : {temp}C")
            print(f"  Condition   : {cond}")
            print(f"  Humidity    : {hum}%")
            print(f"  Wind        : {wind} km/h\n")
            return

        if not temps:
            warn("No data in DB. Use 'fetch <city>' to add cities.")
            return
        print(f"\n  {'CITY':<18} {'TEMP':>7}  {'HUM':>5}  {'WIND':>8}  CONDITION")
        print("  " + "-" * 62)
        for c, t in temps.items():
            cond = self.db.get_registry("condition", c)
            hum  = self.db.get_registry("humidity",  c)
            wind = self.db.get_registry("wind",      c)
            _print_city_row(c, t, hum, wind, cond)
        print()

    def cmd_stats(self, _args: str) -> None:
        temps = self.db.read_all_schemes().get("temperature", {})
        if not temps:
            warn("No data in DB.")
            return
        pairs = [(c, float(t)) for c, t in temps.items()]
        avg   = sum(t for _, t in pairs) / len(pairs)
        hot   = max(pairs, key=lambda x: x[1])
        cold  = min(pairs, key=lambda x: x[1])

        humids = self.db.read_all_schemes().get("humidity", {})
        avg_h  = sum(float(h) for h in humids.values()) / len(humids) if humids else 0

        print(f"\n  Cities tracked  : {len(pairs)}")
        print(f"  Avg temperature : {avg:.1f}C")
        print(f"  Avg humidity    : {avg_h:.1f}%")
        print(f"  Hottest         : {Color.RED}{hot[0]}{Color.END} ({hot[1]}C)")
        print(f"  Coldest         : {Color.BLUE}{cold[0]}{Color.END} ({cold[1]}C)\n")

    def cmd_help(self, _args: str) -> None:
        print(Color.BOLD + "\n  Weather CLI — Commands\n" + Color.END)
        rows = [
            ("fetch  <ciudad>",  "Descargar clima actual (guarda en DB)"),
            ("update <ciudad>",  "Refrescar datos de ciudad existente"),
            ("show   [ciudad]",  "Mostrar tabla o detalle de ciudad"),
            ("stats",            "Resumen estadistico de todas las ciudades"),
            ("help",             "Mostrar esta ayuda"),
            ("exit",             "Guardar y salir"),
        ]
        for cmd, desc in rows:
            print(f"  {Color.CYAN}{cmd:<22}{Color.END} {desc}")
        print()

    def cmd_exit(self, _args: str) -> None:
        self.db.close()
        ok("Weather log saved. Goodbye.")
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
        print(Color.BOLD + "\n  Weather CLI" + Color.END +
              "  (type 'help' for commands)\n")
        cached = len(self.db.read_all_schemes().get("temperature", {}))
        if cached:
            info(f"{cached} cities cached in DB. Type 'show' to display them.")
        else:
            info("DB empty. Try: fetch London")
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
    WeatherCLI().run()
