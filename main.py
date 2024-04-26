from src.database import Database, Data
from src.data_models import types, booleans
from queue import Queue
from threading import Thread
import atexit
import argparse

my_redis: Database = Database('my_db', 2048, 'root', 'root')

class Interpreter(Thread):
    def __init__(self) -> None:
        super().__init__()
        
        self.messages: Queue = Queue()

        Thread(target=self.output_thread, daemon=True).start()
        
    def run(self) -> None:
        while True:
            command_args: list = input('> ').split(' ')
            command_name: str = command_args[0]
            args: list = command_args[1:]
            
            if command_name == 'exit':
                exit(0)
            
            elif command_name == 'debug':
                self.messages.put('DEBUG')
                
            elif command_name == 'add_scheme':
                parsed: list =  self.parse_add_scheme_command(args)
                my_redis.add_scheme(parsed['name'],
                                    parsed['type1'],
                                    parsed['type2'],
                                    parsed['overwrite'],
                                    parsed['size'])
                
            elif command_name == 'set_registry':
                parsed: list = self.parse_set_registry_command(args)
                
                my_redis.insert_into_scheme(parsed['scheme'],
                                            Data(parsed['key'], parsed['value']))
                
            elif command_name == 'get_all_schemes':
                Thread(target=self.get_all_schemes, daemon=True).start()
                
            else:
                raise ValueError('Invalid command')
    
    def read_all_schemes(self, scheme_name: str) -> None:
        self.messages.put(my_redis.read_all_schemes(scheme_name)) 
    
    def parse_add_scheme_command(self, command_args):
        if len(command_args) != 5:
            raise ValueError('Invalid number of arguments for add_scheme command')
        
        return {
            'name': command_args[0],
            'type1': types[command_args[1]],
            'type2': types[command_args[2]],
            'overwrite': booleans[command_args[3]],
            'size': int(command_args[4])
        }

    def parse_set_registry_command(self, command_args):
        if len(command_args) != 3:
            raise ValueError('Invalid number of arguments for set_registry command')
        
        return {
            'scheme': command_args[0],
            'key': command_args[1],
            'value': command_args[2]
        }
        
    def get_all_schemes(self) -> None:
        self.messages.put(my_redis.read_all_schemes())
    
    def output_thread(self) -> None:
        while True:
            if not self.messages.empty():
                print(self.messages.get())
"""
add_scheme users str str True 1024
add_scheme clients str str True 1024
add_scheme cars str str False 1024
get_all_schemes 
set_registry users usuario1 123
set_registry clients usuario1 123
set_registry cars audi 123
"""

interpreter: Interpreter = Interpreter()
interpreter.start()

def at_exit() -> None:
    print('Exiting...')
    my_redis.close()

atexit.register(at_exit)

