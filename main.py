from src.core import Interpreter, InterpreterType
from src.logger import Logger
from uuid import uuid4

"""
create_scheme users str str True 1024
create_scheme clients str str True 1024
create_scheme cars str str False 1024
show_schemes
insert_into users usuario1 123
insert_into clients usuario1 123
insert_into cars audi 123
insert_into users2 hola {"key1": "value1", "key2": "value2", "key3": "value3"}
"""

interpreter: Interpreter = Interpreter(type=InterpreterType.command_line)
interpreter.start()
