from typing import Dict, Tuple
import sys
import os
from src.data_models import *
from src.exceptions import *
from src.dumper import *
from src.utils import getsize

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
    def __init__(self) -> None:
        self._schemes: Dict[str, Scheme] = {"__internal__": Scheme(String, String, True, 2048)}

    def _append_scheme(self, scheme_name: str, scheme: Scheme) -> None:
        if scheme_name in self._schemes.keys():
            raise SchemeAlreadyThere
        
        self._schemes[scheme_name] = scheme

    def _put_into_scheme(self, scheme_name: str, data: Data) -> None:
        if not scheme_name in self._schemes.keys():
            raise InvalidSchemeName
        
        if getsize(self._schemes[scheme_name]) + getsize(data) > self._schemes[scheme_name]._memory_scheme_size_bytes:
            raise SchemeReachedMaxSize
        
        self._schemes[scheme_name].append_data(data)
    
    def _del_scheme(self, scheme_name: str) -> None:
        del(self._schemes[scheme_name])
    
    def _get_all_schemes(self) -> None:
        return {key: self._schemes[key]._data for key in self._schemes.keys()}
    
class Database:
    def __init__(self, db_name: str, memory_scheme_size_mb: int = 1024) -> None:
        self.db_name = db_name
        self.memory_size_mb = memory_scheme_size_mb
        self.schemes: SchemeTable = SchemeTable()  

        self.load_state()
        
    def __getstate__(self):
        state = self.__dict__.copy()

        return state
    
    def load_state(self):
        file_path: str = os.path.join('internal', f'{self.db_name}.{FORMAT}')
        
        if not  os.path.isfile(file_path): return
         
        states: Dict = load(file_path)
        
        self.__dict__.update(states)

    def add_scheme(self, scheme_name: str, key_type: type, vals_type: type, rewrite_keys: bool, scheme_size_mb: int) -> None:
        self.schemes._append_scheme(scheme_name=scheme_name,
                                    scheme=Scheme(key_type=key_type,
                                           vals_type=vals_type,
                                           rewrite_keys=rewrite_keys,
                                           memory_scheme_size_mb=scheme_size_mb))
    
    def insert_into_scheme(self, scheme_name: str, data: Data) -> None:    
        self.schemes._put_into_scheme(scheme_name=scheme_name,
                                      data=data)
        
    def close(self) -> None:
        save(data_file_path=os.path.join('internal', f'{self.db_name}.{FORMAT}'), database=self.__getstate__())
    
    def read_all_schemes(self) -> Dict:
        return self.schemes._get_all_schemes()
    