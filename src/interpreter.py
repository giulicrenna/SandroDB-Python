from src.database import Database, Data, Scheme
from src.data_models import types, booleans
from src.exceptions import *
from src.dumper import save, load, save_generic
from src.logger import Logger
from src.commands import Commands
from queue import Queue
from threading import Thread
import os
import json

COMM: Commands = Commands()

class Databases:
    def __init__(self) -> None:
        self.databases: dict = {}

    def add_database(self, database_name: str, database: Database) -> None:
        if database_name in self.databases.keys():
            raise DatabaseAlreadyThere
        
        self.databases[database_name] = database

    def get_database(self, database_name: str) -> Database:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name]

    def remove_database(self, database_name: str) -> None:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        del self.databases[database_name]

    def get_all_databases(self) -> list:
        return list(self.databases.keys())

    def get_database_size(self, database_name: str) -> int:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name].get_size()

    def get_database_max_size(self, database_name: str) -> int:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name].get_max_size()

    def get_database_schemes(self, database_name: str) -> list:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name].get_schemes()

    def get_database_scheme_size(self, database_name: str, scheme_name: str) -> int:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name].get_scheme_size(scheme_name)

    def get_database_scheme_max_size(self, database_name: str, scheme_name: str) -> int:
        if database_name not in self.databases.keys():
            raise DatabaseDoesNotExist

        return self.databases[database_name].get_scheme_max_size(scheme_name)
    
    def close_all(self) -> None:
        for database in self.databases.values():
            database.close()

my_redis: Database = Database('my_db', 2048, 'root', 'root')

Logger.print_log_normal(log='Database started succesfully', instance='main')

class Parser:
    @staticmethod
    def parse_add_scheme_command(command_args: list) -> dict | None:
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
    def parse_set_registry_command(command_args: list) -> dict | None:
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
    def parse_get_registry_command(command_args: list) -> dict | None:
        if len(command_args) != 2:
            Logger.print_log_error('Invalid number of arguments for get_registry command', 'parse_get_registry_command')
            return

        return {
            'scheme': command_args[0],
            'key': command_args[1]
        }
    
    @staticmethod
    def parse_add_new_database(command_args: list) -> dict:
        if len(command_args) != 2:
            Logger.print_log_error('Invalid number of arguments for add_new_database command', 'parse_add_new_database')
            return
        
        try:
            return {
                'name': command_args[0],
                'size': int(command_args[1])
            }
        except Exception as e:
            Logger.print_log_error('Invalid arguments for add_new_database command', 'parse_add_new_database')
            return
        
    @staticmethod 
    def parse_use_database(command_args: list) -> dict:
        if len(command_args) != 1:
            Logger.print_log_error('Invalid number of arguments for use_database command', 'parse_use_database')
            return
        
        return {
            'name': command_args[0]
        }

    
class Interpreter(Thread):
    def __init__(self) -> None:
        super().__init__()
        
        self.messages: Queue = Queue()
        self.data_bases: Databases = self.load_databases()
        self.current_db: Database | None = None
        
        Thread(target=self.output_thread, daemon=True).start()
        
    def run(self) -> None:
        if len(self.data_bases.databases.keys()) == 1:
            Logger.print_log_warning('Setting up the unique database as selected.')
            self.current_db = self.data_bases.databases[list(self.data_bases.databases.keys())[0]]
            
        while True:
            command_args: list = input('\n> ').split(' ')
            
            command_name: str = command_args[0]
            
            args: list = command_args[1:]
            
            self.interpretate(command_name=command_name,
                                args=args)
    
    def interpretate(self, command_name: str, args: list) -> None:
        try:
            if command_name == COMM.EXIT[0]:
                exit(0)
            
            elif command_name == COMM.HELP[0]:
                COMM.show_help()
            
            elif command_name == COMM.CLEAR[0]:
                os.system('cls' if os.name == 'nt' else 'clear')
                return
            
            elif command_name == COMM.DEBUG[0]:
                self.messages.put('DEBUG')           
            # Here below are all the database control commands
            
            elif command_name == COMM.CREATE_DB[0]:
                parsed: dict = Parser.parse_add_new_database(args)
                
                if parsed is None:
                    return
                
                new_db: Database = Database(parsed['name'],
                                parsed['size'],
                                'root',
                                'root')
                
                self.data_bases.add_database(database_name=parsed['name'],
                                            database=new_db)          
            
            elif command_name == COMM.USE_DB[0]:
                parsed: dict = Parser.parse_use_database(args)
                
                if parsed is None:
                    DatabaseDoesNotExist
                
                if not parsed['name'] in self.data_bases.databases.keys():
                    raise DatabaseDoesNotExist
                
                self.current_db = self.data_bases.databases[parsed['name']]
            
            elif command_name == COMM.SHOW_DATABASES[0]:
                available_databases: str = '\nAvailable databases: '
                
                for database_name in self.data_bases.databases.keys():
                    available_databases += f'\n{database_name}'
                
                self.messages.put(available_databases)
                 
            # Here below all the scheme and registry control commands are implemented
            elif command_name == COMM.CREATE_SCHEME[0]:
                parsed: dict =  Parser.parse_add_scheme_command(args)

                if parsed is None:
                    return
                
                if self.current_db is None:
                    raise DatabaseDoNotSelected
                
                self.current_db.add_scheme(parsed['name'],
                                    parsed['type1'],
                                    parsed['type2'],
                                    parsed['overwrite'],
                                    parsed['size'])
                    
            elif command_name == COMM.INSERT_INTO[0]:
                parsed: list = Parser.parse_set_registry_command(args)
                
                if parsed is None:
                    return
                
                if self.current_db is None:
                    raise DatabaseDoNotSelected
                
                scheme_name: str = parsed['scheme']
                
                if not scheme_name in self.current_db.schemes_table._schemes.keys():
                    raise InvalidSchemeName
                
                scheme: Scheme = self.current_db.schemes_table._schemes[scheme_name]
                
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
                
                self.current_db.insert_into_scheme(parsed['scheme'],
                                            Data(parsed['key'], parsed['value']))
                    
            elif command_name == COMM.SHOW_SCHEMES[0]:
                Thread(target=self.get_schemes_name, daemon=True).start()
                    
            elif command_name == COMM.GET_ALL_REGISTRY[0]:
                Thread(target=self.get_all_schemes, daemon=True).start()
                
            elif command_name == COMM.GET_REGISTRY[0]:
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
        
        except DatabaseDoNotSelected:
            Logger.print_log_error(f'Database not selected', 'interpretate')
            return
        
        except DatabaseDoesNotExist:
            Logger.print_log_error(f'Database does not exist', 'interpretate')
            return

        except KeyError:
            Logger.print_log_error(f'Bad command usage, check help.', 'interpretate')
            return
        
    def load_databases_at_startup(self) -> None:
        databases_path = os.path.join(os.getcwd(), '')
        save()

    def get_schemes_name(self) -> None:
        if self.current_db == None:
            Logger.print_log_error('Database not selected', 'get_all_schemes')
            return
        
        self.messages.put(str(list(self.current_db.schemes_table._schemes.keys())))
    
    def get_registry(self, scheme_name: str, key: str) -> None:
        if self.current_db == None:
            Logger.print_log_error('Database not setted', 'get_registry')
            return
        try:
            self.messages.put(self.current_db.get_registry(scheme_name, key))        
        except KeyNotFound:
            Logger.print_log_error(f'Key {key} does not exist', 'get_registry')
            return
        except InvalidSchemeName:
            Logger.print_log_error(f'Scheme {scheme_name} does not exist', 'get_registry')
            return
        
    def get_all_schemes(self) -> None:
        if self.current_db == None:
            Logger.print_log_error('Database not setted', 'get_all_schemes')
            return
        
        self.messages.put(str(self.current_db.read_all_schemes()))
    
    def output_thread(self) -> None:
        while True:
            if not self.messages.empty():
                if self.current_db != None:
                    Logger.print_database_output(self.current_db.db_name, self.messages.get())
                else:
                    Logger.print_database_output('', self.messages.get())
    
    def save_databases_stack(self) -> None:
        internal_path = os.path.join(os.getcwd(), 'internal', 'db_stack.property')
        
        save_generic(internal_path, self.data_bases)
    
    def load_databases(self) -> Databases:
        if not os.path.exists(os.path.join(os.getcwd(), 'internal', 'db_stack.property')):
            return Databases()
        
        return load(os.path.join(os.getcwd(), 'internal', 'db_stack.property'))
            
    def at_close(self) -> None:
        Logger.print_log_warning('Closing database')
        
        self.save_databases_stack()
        self.data_bases.close_all()
    
    