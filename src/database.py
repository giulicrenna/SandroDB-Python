from src.privileges import Privileges, PrivilegesScheme
from src.user import User, UserScheme
from src.data_models import *
from src.exceptions import *
from src.dumper import *
from src.utils import getsize, threaded
from typing import Dict, Tuple
import sys
import os

FORMAT: str = "MKDB"

mb_to_bytes = lambda mb_: mb_ * 1024**2
bytes_to_mb = lambda bytes_: bytes_ / 1024**2 

class Data:
    def __init__(self, key_name: any, value: any) -> None:
        self.types: Tuple[type, type] = (type(key_name), type(value))
        self.data: Tuple[any, any] = (key_name, value)
        
class Scheme:
    def __init__(self, key_type: type, 
                 vals_type: type,
                 rewrite_keys: bool,
                 memory_scheme_size_mb: int) -> None:
        
        self._memory_scheme_size_bytes = mb_to_bytes(memory_scheme_size_mb)
        self._key_type = key_type
        self._vals_type = vals_type
        self._rewrite_keys = rewrite_keys
        self._data: Dict[key_type, vals_type] = {}
        self._privileges_scheme: PrivilegesScheme = PrivilegesScheme()
        
    def append_data(self, data_portion: Data) -> None:
        if self._key_type != data_portion.types[0] or self._vals_type != data_portion.types[1]:
            raise InvalidDataTypeException
        
        if not self._rewrite_keys:
            if data_portion.data[0] in self._data.keys():
                return
            
            self._data[data_portion.data[0]] = data_portion.data[1]
            return
        
        self._data[data_portion.data[0]] = data_portion.data[1]

    def _get_scheme_size(self) -> int:
        return getsize(self._data)
    
class SchemeTable:
    def __init__(self,
                 user: User,
                 privileges_scheme: PrivilegesScheme) -> None:
        self.user: User = user
        self.privileges_scheme: PrivilegesScheme = privileges_scheme
        self.current_user_privileges: Privileges = self.privileges_scheme.get_privileges(user=self.user)
        
        self._schemes: Dict[str, Scheme] = {"__internal__": Scheme(String, String, True, 2048)}
        self.privileges_scheme: PrivilegesScheme = PrivilegesScheme()
            
    def _append_scheme(self, scheme_name: str, scheme: Scheme) -> None:
        if not self.current_user_privileges.ADD_SCHEME:
            raise NotEnoughPrivileges
        
        if scheme_name in self._schemes.keys():
            raise SchemeAlreadyThere
        
        self._schemes[scheme_name] = scheme

    def _put_into_scheme(self, scheme_name: str, data: Data) -> None:
        if not self.current_user_privileges.ADD_REGISTRY:
            raise NotEnoughPrivileges
        
        if not scheme_name in self._schemes.keys():
            raise InvalidSchemeName
        
        if getsize(self._schemes[scheme_name]) + getsize(data) > self._schemes[scheme_name]._memory_scheme_size_bytes:
            raise SchemeReachedMaxSize
        
        self._schemes[scheme_name].append_data(data)
    
    def _del_scheme(self, scheme_name: str) -> None:
        if not self.current_user_privileges.DEL_SCHEME:
            raise NotEnoughPrivileges
        
        del(self._schemes[scheme_name])
    
    def _get_all_schemes(self) -> None:
        if not self.current_user_privileges.GET_ALL_SCHEMES:
            raise NotEnoughPrivileges
        
        return {key: self._schemes[key]._data for key in self._schemes.keys()}
    
    def _get_registry(self, scheme_name: str, key: any) -> None:
        if not self.current_user_privileges.READ_SCHEME:
            raise NotEnoughPrivileges
        
        if not scheme_name in self._schemes.keys():
            raise InvalidSchemeName
        
        if not type(key) == self._schemes[scheme_name]._key_type:
            raise InvalidKeyType
        
        if not key in self._schemes[scheme_name]._data.keys():
            raise KeyNotFound
        
        scheme: Scheme = self._schemes[scheme_name]
        
        return scheme._data[key]
        
class Database:
    def __init__(self,
                 db_name: str,
                 memory_scheme_size_mb: int,
                 user: str,
                 password: str) -> None:
        self.db_name = db_name
        self.memory_size_mb = memory_scheme_size_mb
        self.privileges_scheme: PrivilegesScheme = PrivilegesScheme()
        self.user_scheme: UserScheme = UserScheme()
        self.user: User = self.user_scheme.get_user(user)
        
        self.check_root()
        
        self.schemes_table: SchemeTable = SchemeTable(user=self.user,
                                                      privileges_scheme=self.privileges_scheme)
        self.current_user_privileges: Privileges = self.privileges_scheme.get_privileges(user=self.user)
        
        self.load_state()
        
        if not self.user.validate_password(password):
            raise InvalidPasswordException
        
        if not os.path.isdir('internal'):
            os.mkdir('internal')
        
    def __getstate__(self):
        state = self.__dict__.copy()

        return state
    
    def check_root(self) -> None:
        if not "root" in self.privileges_scheme.get_all_users():
            root_privileges = Privileges()
            root_privileges.make_root()
            root: User = self.user_scheme.get_user("root")
            
            self.privileges_scheme.add_privilege(user=root,
                                                  privileges=root_privileges)
    
    def load_state(self):
        file_path: str = os.path.join('internal', f'{self.db_name}.{FORMAT}')
        
        if not  os.path.isfile(file_path): return
         
        states: Dict = load(file_path)
        
        del(states['user'])
        
        self.__dict__.update(states)

    def add_scheme(self, scheme_name: str, key_type: type, vals_type: type, rewrite_keys: bool, scheme_size_mb: int) -> None:
        self.schemes_table._append_scheme(scheme_name=scheme_name,
                                    scheme=Scheme(key_type=key_type,
                                           vals_type=vals_type,
                                           rewrite_keys=rewrite_keys,
                                           memory_scheme_size_mb=scheme_size_mb))
    
    def insert_into_scheme(self, scheme_name: str, data: Data) -> None:    
        self.schemes_table._put_into_scheme(scheme_name=scheme_name,
                                      data=data)
        
    def close(self) -> None:
        save(data_file_path=os.path.join('internal', f'{self.db_name}.{FORMAT}'), database=self.__getstate__())
    
    def read_all_schemes(self) -> Dict:
        return self.schemes_table._get_all_schemes()
    
    def get_registry(self, scheme_name: str,
                     key: any) -> any:
        return self.schemes_table._get_registry(scheme_name=scheme_name, key=key)
    
    def delete_scheme(self, scheme_name: str) -> None:
        self.schemes_table._del_scheme(scheme_name=scheme_name)
    
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
        