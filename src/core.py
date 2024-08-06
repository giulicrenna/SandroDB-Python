from src.database import Database, Scheme, Data
from src.data_models import types, booleans
from src.exceptions import *
from src.user import User, UserScheme, calculate_sha256
from src.privileges import PrivilegesScheme, Privileges
from src.dumper import load, save_generic
from src.logger import Logger
from src.commands import Commands
from queue import Queue
from threading import Thread
from typing import Callable, Tuple, Dict
import os
import json

AUTHOR: str = 'Giuliano Crenna'

COMM: Commands = Commands()

Logger.print_log_normal(log='Database started succesfully', instance='main')

class Instances:
    auth: str = 'Auth'
    user_management: str = 'User management'
    database_management: str = 'Database management'
    database_exception: str = 'Database Exception'
    scheme_management: str = 'Scheme management'
    scheme_exception: str = 'Scheme Exception'
    registry_management: str = 'Registry management'
    registry_exception: str = 'Registry Exception'
    help: str = 'Help'
    debug: str = 'Debug'

class Databases:
    def __init__(self) -> None:
        self.databases: dict = self.load_databases()

    def load_databases(self) -> list[str]:
        return [db.split('.')[0] for db in os.listdir(os.path.join(os.getcwd(), 'internal')) if db != 'core.property']

    def get_database(self, database_name: str, user: User) -> Database:
        if database_name not in self.databases:
            raise DatabaseDoesNotExist

        return Database(db_name=database_name, user=user)

    def remove_database(self, database_name: str) -> None:
        if database_name not in self.databases:
            raise DatabaseDoesNotExist

        del self.databases[database_name]

    def get_all_databases(self) -> list:
        return self.databases

    def get_database_size(self, database_name: str) -> int:
        if database_name not in self.databases:
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
        if len(command_args) != 1:
            Logger.print_log_error('Invalid number of arguments for add_new_database command', 'parse_add_new_database')
            return
        
        try:
            return {
                'name': command_args[0],
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
        
    @staticmethod 
    def parse_login(command_args: list) -> dict:
        if len(command_args) != 2:
            Logger.print_log_error('Invalid number of arguments for use_database command', 'parse_use_database')
            return
        
        return {
            'username': command_args[0],
            'password': command_args[1]
        }
        
    @staticmethod 
    def parse_del_scheme(command_args: list) -> dict:
        if len(command_args) != 1:
            Logger.print_log_error('Invalid number of arguments for use_database command', 'parse_use_database')
            return
        
        return {
            'scheme_name': command_args[0]
        }
   
class InterpreterType:
    server: str = 'server'
    command_line: str = 'command_line'
    
class VirtualMemory:
    def __init__(self) -> None:
        self.connections: Dict[int, Database] = {}
        
    def get_database_from_uuid(self, conn_id: int) -> Database:
        if conn_id not in self.connections.keys():
            self.connections[conn_id] = None
            return
        
        return self.connections[conn_id]

    def add_conn_id(self, conn_id: int) -> None:
        if conn_id not in self.connections.keys():
            self.connections[conn_id] = None
            return
    
    def change_database_state(self, conn_id: int, database: Database) -> None:
        self.connections[conn_id] = database
        return
    
class Interpreter(Thread):
    def __init__(self, type: str,
                 virtual_memory: VirtualMemory,
                 conn_id: int) -> None:
        """
        Atributes starting with a _ won't be saved
        """
        super().__init__()
        """
        Interpreter Type is used to determine
        how the IO of the interpreter will work. 
        
        _command_queue has elements of the type Tuple[Tuple[str, str], str]:
            - Command and args.
            - UUID
        """
        self._type: str = type
        self._command: str | None =  None
        self._command_queue: Queue = Queue()
        self._server_output_callback: Callable[[str]] = None
        self._should_stop: bool = False
        """
        Interpreter IO
        """
        self._messages: Queue = Queue()
        self._data_bases: Databases = Databases()
        self.conn_id = conn_id
        self.virtual_memory: VirtualMemory = virtual_memory
        self._current_db: Database = self.virtual_memory.get_database_from_uuid(self.conn_id)
        
        """
        Creates the schemes to manage the users.
        """
        self._user: User = None
        self.user_scheme: UserScheme = UserScheme()
        self.privileges_scheme: PrivilegesScheme = PrivilegesScheme()
        
        
        Thread(target=self.output_thread, daemon=True).start()
        
        self.load_state()
        
    def run(self) -> None:
        while True and not self._should_stop:
            try:
                if self._type == InterpreterType.command_line:
                    self._command: list = input('\n> ').split(' ')
                    
                    command_name: str = self._command[0]
                    
                    args: list = self._command[1:]
                    
                    self.interpretate(command_name=command_name,
                                        args=args)
                elif self._type == InterpreterType.server:
                    while not self._command_queue.empty():   
                        command: Tuple[str, str] = self._command_queue.get()
                        
                        command_name: str = command[0]
                        
                        args: list = command[1:]
                        
                        self.interpretate(command_name=command_name,
                                        args=args)
            except Exception as e:
                Logger.print_log_error(str(e),'Main Thread')
                self.save_databases_stack()
                self._should_stop = True
            
    def add_command_task(self, command: str) -> None:
        if self._type == InterpreterType.server:
            self._command_queue.put(command.split(' '))
            return
        
        Logger.print_log_error('Interpreter type is not a server', 'add_command_task')
        
    def set_output_callback(self, callback: Callable) -> None:
        if self._type == InterpreterType.server:
            self._server_output_callback = callback
            return
        
        Logger.print_log_error('Interpreter type is not server', 'set_output_callback')
            
    def check_root(self) -> None:
        if not self._user in self.privileges_scheme.get_all_users() and self._user.name == 'root':
            root_privileges = Privileges()
            root_privileges.make_root()
            
            self.privileges_scheme.add_privilege(user=self._user,
                                                  privileges=root_privileges)
        
        if self._user.password == calculate_sha256('root'):
            Logger.print_log_warning('change root password for better security.')

    def add_user(self, user_name: str,
                 password: str) -> None:
        if not self.current_user_privileges.ADD_USER:
            raise NotEnoughPrivileges
        
        new_user: User = User(name=user_name)
        new_user.set_password(password=password)
        self.user_scheme.add_user(user=new_user)
        self.privileges_scheme.add_privileges(user=new_user,
                                              privileges=Privileges())
    
    def delete_user(self, user: User) -> None:
        if not self.current_user_privileges.DEL_USER:
            raise NotEnoughPrivileges
        
        self.user_scheme.remove_user(user=user)

    def get_schemes_name(self) -> None:
        if self._current_db == None:
            self.load_msg('Database not selected', Instances.database_exception)
            Logger.print_log_error('Database not selected', 'get_all_schemes')
            return
        
        self.load_msg(str(list(self._current_db.schemes_table._schemes.keys())), Instances.scheme_management)
    
    def get_registry(self, scheme_name: str, key: str) -> None:
        if self._current_db == None:
            self.load_msg('Database not selected', Instances.database_exception)
            Logger.print_log_error('Database not setted', Instances.database_exception)
            return
        try:
            self.load_msg(self._current_db.get_registry(scheme_name, key), Instances.registry_exception)      
        except KeyNotFound:
            self.load_msg(f'Key {key} does not exist', Instances.registry_exception)
            Logger.print_log_error(f'Key {key} does not exist', Instances.registry_exception)
            return
        except InvalidSchemeName:
            self.load_msg(f'Scheme {scheme_name} does not exist', Instances.scheme_exception)
            Logger.print_log_error(f'Scheme {scheme_name} does not exist', Instances.scheme_exception)
            return
        
    def get_all_schemes(self) -> None:
        if self._current_db == None:
            self.load_msg('Database not selected', Instances.database_exception)
            Logger.print_log_error('Database not setted', Instances.database_exception)
            return
        
        self.load_msg(str(self._current_db.read_all_schemes()), Instances.scheme_management)
    
    def output_thread(self) -> None:
        while True:
            if not self._messages.empty() and self._type == InterpreterType.command_line:
                if self._current_db != None:
                    Logger.print_database_output(self._current_db.db_name, self._messages.get()[0])
                else:
                    Logger.print_database_output('', self._messages.get())
            elif not self._messages.empty() and self._type == InterpreterType.server:
                message: Tuple[str, str] = self._messages.get()
                self._server_output_callback(message, self.conn_id)
            
    def save_databases_stack(self) -> None:
        internal_path = os.path.join(os.getcwd(), 'internal', 'core.property')
        
        state = self.__dict__.copy()
        
        for key in list(state.keys()):
            if key[0] == '_':
                del(state[key])

        save_generic(internal_path, state)
    
    def load_state(self):
        file_path: str = os.path.join('internal', 'core.property')
        
        if not  os.path.isfile(file_path): return
         
        states: dict = load(file_path)
        
        self.__dict__.update(states)
    
    def at_close(self) -> None:
        Logger.print_log_warning('Closing database')
        
        self.save_databases_stack()
        
        if self._current_db is not None:
            self._current_db.close()
    
    def load_msg(self, message: str, instance: str) -> None:
        new_message: str = f'[{instance}]\t{message}\n'
        
        self._messages.put(new_message)
    
    def interpretate(self, command_name: str, args: list) -> None:
        try:
            if command_name == COMM.EXIT[0]:
                self.save_databases_stack()
        
                if self._current_db is not None:
                    self._current_db.close()
                
                exit(0)

            if command_name == COMM.LOGIN[0]:
                parsed: dict = Parser.parse_login(args)
                
                if parsed is None:
                    return
                
                username: str = parsed['username']
                self._user = self.user_scheme.get_user(name=username,
                                                       password=parsed['password'])
                
                self.check_root()

                self.load_msg(f'Login as {username}', Instances.auth)
                
                return
               
            if self._user is None:
                self.load_msg('Must login', Instances.auth)
                Logger.print_log_error('Must login', 'core')
                return

            elif command_name == COMM.LOGOUT[0]:
                self._user = None
                self.load_msg(f'Logged out as {self._user.name}', Instances.auth)
                return
            
            elif command_name == COMM.SHOW_USERS[0]:
                if not self.privileges_scheme.get_privileges(user=self._user).READ_PRIVILEGE:
                    raise NotEnoughPrivileges
                
                users: list[User] = self.user_scheme.get_all_users()
                msg: list[str] = [user.name for user in users]
                
                self.load_msg(str(msg), Instances.user_management)

                return
            
            if command_name == COMM.HELP[0]:
                self.load_msg(COMM.show_help(), Instances.help)
                    
            elif command_name == COMM.CLEAR[0]:
                os.system('cls' if os.name == 'nt' else 'clear')
                return
            
            elif command_name == COMM.DEBUG[0]:
                self.load_msg('DEBUG MESSAGE', Instances.debug)
            # Here below are all the database control commands
            
            elif command_name == COMM.CREATE_DB[0]:
                parsed: dict = Parser.parse_add_new_database(args)
                db_name: str = parsed['name']
                
                if parsed is None:
                    return
                
                Database(db_name = db_name, user=self._user).close()
                
                self.load_msg(f'Database with name: {db_name} created succesfully', Instances.database_management)
                
            elif command_name == COMM.USE_DB[0]:
                parsed: dict = Parser.parse_use_database(args)
                db_name: str = parsed['name']
                
                databases: Databases = Databases()
                
                if parsed is None:
                    DatabaseDoesNotExist # change this
                    return
                
                if not db_name in databases.databases:
                    self.load_msg(f'Database with name: {db_name} does not exist', Instances.database_exception)
                    raise DatabaseDoesNotExist
                
                if self._current_db is not None:
                    self._current_db.close()                

                new_db: Database = self._data_bases.get_database(database_name=parsed['name'],
                                                                 user=self._user)

                self.virtual_memory.change_database_state(conn_id=self.conn_id,
                                                          database=new_db)
                
                self._current_db = self.virtual_memory.get_database_from_uuid(conn_id=self.conn_id)
                
                self.load_msg(f'Database with name: {db_name} selected', Instances.database_management)
                
            elif command_name == COMM.SHOW_DATABASES[0]:
                available_databases: str = 'Available databases: '
                
                databases: Databases = Databases()                
                
                for database_name in databases.databases:
                    available_databases += f'\t{database_name}'
                
                self.load_msg(available_databases, Instances.database_management)
                 
            # Here below all the scheme and registry control commands are implemented
            elif command_name == COMM.CREATE_SCHEME[0]:
                parsed: dict =  Parser.parse_add_scheme_command(args)
                scheme_name: str = parsed['name']
                
                if parsed is None:
                    return
                
                if self._current_db is None:
                    raise DatabaseDoNotSelected
                
                self._current_db.add_scheme(scheme_name,
                                    parsed['type1'],
                                    parsed['type2'],
                                    parsed['overwrite'],
                                    parsed['size'])
                
                self.load_msg(f'Scheme with name: {scheme_name} created succesfully', Instances.scheme_management)
                    
            elif command_name == COMM.INSERT_INTO[0]:
                parsed: list = Parser.parse_set_registry_command(args)
                
                if parsed is None:
                    return
                
                if self._current_db is None:
                    raise DatabaseDoNotSelected
                
                scheme_name: str = parsed['scheme']
                
                if not scheme_name in self._current_db.schemes_table._schemes.keys():
                    raise InvalidSchemeName
                
                scheme: Scheme = self._current_db.schemes_table._schemes[scheme_name]
                
                key_type, value_type = scheme._key_type, scheme._vals_type
                
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
                    self.load_msg('Invalid type for key or value', Instances.registry_exception)
                    return
                
                self._current_db.insert_into_scheme(parsed['scheme'],
                                            Data(parsed['key'], parsed['value']))
                
                self.load_msg(...)
                    
            elif command_name == COMM.SHOW_SCHEMES[0]:
                Thread(target=self.get_schemes_name, daemon=True).start()
                    
            elif command_name == COMM.DEL_SCHEME[0]:
                parsed: dict = Parser.parse_del_scheme(args)
                scheme_name: str = parsed['scheme_name']
                
                self._current_db.delete_scheme(scheme_name)
                
                self.load_msg(f'Scheme with name: {scheme_name} deleted succesfully', Instances.scheme_management)
                    
            elif command_name == COMM.GET_ALL_REGISTRY[0]:
                Thread(target=self.get_all_schemes, daemon=True).start()
                
            elif command_name == COMM.GET_REGISTRY[0]:
                parsed: list = Parser.parse_get_registry_command(args)
                
                if parsed is None:
                    return
                
                Thread(target=self.get_registry,
                    args=(parsed['scheme'], parsed['key'],),
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
        
        except Exception as e:
            Logger.print_log_error(f'Unknown error: {e}', 'interpretate')
            return
        
        