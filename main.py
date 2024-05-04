from src.database import Database
from src.data_models import types, booleans
from src.exceptions import *
from src.interpreter import Interpreter
from src.logger import Logger
import atexit

"""
create_scheme users str str True 1024
create_scheme clients str str True 1024
create_scheme cars str str False 1024
get_all_schemes 
insert_into users usuario1 123
insert_into clients usuario1 123
insert_into cars audi 123
insert_into users2 hola {"key1": "value1", "key2": "value2", "key3": "value3"}
"""

interpreter: Interpreter = Interpreter()
interpreter.start()

def at_exit() -> None:
    Logger.print_log_normal('Closing database', 'main')
    interpreter.at_close()

atexit.register(at_exit)