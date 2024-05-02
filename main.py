from src.database import Database, Data, Scheme
from src.data_models import types, booleans
from src.exceptions import *
from src.logger import Logger
from queue import Queue
from threading import Thread
import atexit
import os
import json

my_redis: Database = Database('my_db', 2048, 'root', 'root')

Logger.print_log_normal(log='Database started succesfully', instance='main')

class Parser:
    @staticmethod
    def parse_add_scheme_command(command_args) -> dict | None:
        if len(command_args) != 5:
            Logger.print_log_error('Invalid number of arguments for add_scheme command', 'parse_add_scheme_command')
            return 
                
        return {
            'name': command_args[0],
            'type1': types[command_args[1]],
            'type2': types[command_args[2]],
            'overwrite': booleans[command_args[3]],
            'size': int(command_args[4])
        }

    @staticmethod
    def parse_set_registry_command(command_args) -> dict | None:
        command_args = ' '.join(command_args).split(' ', 2)
        
        if len(command_args) != 3:
            Logger.print_log_error('Invalid number of arguments for insert_into command', 'parse_set_registry_command')
            return
        
        return {
            'scheme': command_args[0],
            'key': command_args[1],
            'value': command_args[2]
        }
    
    @staticmethod
    def parse_get_registry_command(command_args) -> dict | None:
        if len(command_args) != 2:
            Logger.print_log_error('Invalid number of arguments for get_registry command', 'parse_get_registry_command')
            return

        return {
            'scheme': command_args[0],
            'key': command_args[1]
        }
    
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
            
            self.interpretate(command_name=command_name,
                              args=args)
    
    def interpretate(self, command_name: str, args: list) -> None:
        try:
            if command_name == 'exit':
                    exit(0)
            
            elif command_name == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                return
            
            elif command_name == 'debug':
                self.messages.put('DEBUG')
                
            elif command_name == 'add_scheme':
                parsed: list =  Parser.parse_add_scheme_command(args)

                if parsed is None:
                    return
                
                my_redis.add_scheme(parsed['name'],
                                    parsed['type1'],
                                    parsed['type2'],
                                    parsed['overwrite'],
                                    parsed['size'])
                    
            elif command_name == 'insert_into':
                parsed: list = Parser.parse_set_registry_command(args)
                
                if parsed is None:
                    return
                
                scheme_name: str = parsed['scheme']
                
                if not scheme_name in my_redis.schemes_table._schemes.keys():
                    raise InvalidSchemeName
                
                scheme: Scheme = my_redis.schemes_table._schemes[scheme_name]
                
                key_type, value_type = scheme._key_type, scheme._vals_type
                
                Logger.print_log_debug(f'Key type: {key_type}, value type: {value_type}')
                
                try:
                    if key_type == dict:
                        parsed['key'] = json.loads(parsed['key'])
                    else:
                        parsed['key'] = key_type(parsed['key'])

                    if value_type == dict:
                        parsed['value'] = json.loads(parsed['value'])
                    else:
                        parsed['value'] = value_type(parsed['value'])
                except:
                    Logger.print_log_error(f'Invalid type for key or value', 'set_registry')
                    return
                
                my_redis.insert_into_scheme(parsed['scheme'],
                                            Data(parsed['key'], parsed['value']))
                    
            elif command_name == 'get_all_schemes':
                Thread(target=self.get_all_schemes, daemon=True).start()
                
            elif command_name == 'get_registry':
                parsed: list = Parser.parse_get_registry_command(args)
                
                if parsed is None:
                    return
                
                Thread(target=self.get_registry,
                    args=(parsed['scheme'], parsed['key']),
                    daemon=True).start()
                
            
            else:
                Logger.print_log_warning(f'Invalid command: {command_name}')
                return
            
        except InvalidTypeException:
            Logger.print_log_error(f'Invalid type', 'interpretate')
            return
        
        except InvalidArraySize:
            Logger.print_log_error(f'Invalid array size', 'interpretate')
            return
        
        except InvalidInnerType:
            Logger.print_log_error(f'Invalid inner type', 'interpretate')
            return
        
        except SchemeAlreadyThere:
            Logger.print_log_error(f'Scheme already exists', 'interpretate')
            return
        
        except InvalidDataTypeException:
            Logger.print_log_error(f'Invalid data type', 'interpretate')
            return
        
        except SchemeReachedMaxSize:
            Logger.print_log_error(f'Scheme reached max size', 'interpretate')
            return
        
        except InvalidSchemeName:
            Logger.print_log_error(f'Invalid scheme name', 'interpretate')
            return
        
        except PasswordAlreadySetted:
            Logger.print_log_error(f'Password already setted', 'interpretate')
            return
        
        except PasswordNotSetted:
            Logger.print_log_error(f'Password not setted', 'interpretate')
            return
        
        except UserPrivilegesAlreadySetted:
            Logger.print_log_error(f'User privileges already setted', 'interpretate')
            return
        
        except UserPrivilegesNotSetted:
            Logger.print_log_error(f'User privileges not setted', 'interpretate')
            return
        
        except InvalidPasswordException:
            Logger.print_log_error(f'Invalid password', 'interpretate')
            return
        
        except UserAlreadyExists:
            Logger.print_log_error(f'User already exists', 'interpretate')
            return
        
        except UserDoesNotExist:
            Logger.print_log_error(f'User does not exist', 'interpretate')
            return

        except RootUserCannotBeRemoved:
            Logger.print_log_error(f'Root user cannot be removed', 'interpretate')
            return

        except InvalidUserException:
            Logger.print_log_error(f'Invalid user', 'interpretate')
            return

        except NotEnoughPrivileges:
            Logger.print_log_error(f'Not enough privileges', 'interpretate')
            return

        except InvalidKeyType:
            Logger.print_log_error(f'Invalid key type', 'interpretate')
            return
            
        except KeyNotFound:
            Logger.print_log_error(f'Key not found', 'interpretate')
            return

        except KeyboardInterrupt:
            Logger.print_log_normal('Keyboard interrupt', 'interpretate')
            exit()
        
    def get_registry(self, scheme_name: str, key: str) -> None:
        try:
            self.messages.put(my_redis.get_registry(scheme_name, key))        
        except KeyNotFound:
            Logger.print_log_error(f'Key {key} does not exist', 'get_registry')
            return
        except InvalidSchemeName:
            Logger.print_log_error(f'Scheme {scheme_name} does not exist', 'get_registry')
            return
        
    def get_all_schemes(self) -> None:
        self.messages.put(my_redis.read_all_schemes())
    
    def output_thread(self) -> None:
        while True:
            if not self.messages.empty():
                Logger.print_database_output(self.messages.get())
"""
add_scheme users str str True 1024
add_scheme clients str str True 1024
add_scheme cars str str False 1024
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
    my_redis.close()

atexit.register(at_exit)

