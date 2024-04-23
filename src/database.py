from typing import Dict, Tuple
import sys
import os
from src.data_models import *
from src.exceptions import *
from src.dumper import *

bytes_to_mb = lambda bytes_: bytes_ / 1e6 

class Data:
    def __init__(self, key_name: any, value: any) -> None:
        self.types: Tuple[type, type] = (type(key_name), type(value))
        self.data: Tuple[any, any] = (key_name, value)

class Scheme:
    def __init__(self, key_type: type, 
                 vals_type: type,
                 rewrite_keys: bool,
                 memory_scheme_size_mb: int) -> None:
        
        self._memory_scheme_size_mb = memory_scheme_size_mb
        self._key_type = key_type
        self._vals_type = vals_type
        self._rewrite_keys = rewrite_keys
        self._data: Dict[key_type, vals_type] = {}
    
    def append_data(self, data_portion: Data) -> None:
        if self._get_scheme_size() > self._memory_scheme_size_mb:
            raise SchemeReachedMaxSize
        
        if self._key_type != data_portion.types[0] or self._vals_type != data_portion.types[1]:
            raise InvalidDataTypeException
        
        if self._rewrite_keys:
            if data_portion.data[0] in self._data.keys():
                return
            
            self._data[data_portion.data[0]] = data_portion.data[1]
            return
        
        self._data[data_portion.data[0]] = data_portion.data[1]

    def _get_scheme_size(self) -> int:
        return bytes_to_mb(sys.getsizeof(self._data))
    
class SchemeTable:
    def __init__(self) -> None:
        self._schemes: Dict[str, Scheme] = {"__internal__": Scheme(String)}

    def _append_scheme(self, scheme_name: str, scheme: Scheme) -> None:
        if scheme_name in self._schemes.keys():
            raise SchemeAlreadyThere
        
        self._schemes[scheme_name] = scheme

    def _del_scheme(self, scheme_name: str) -> None:
        del(self._schemes[scheme_name])

class Database:
    def __init__(self, db_name: str, memory_scheme_size_mb: int = 1024) -> None:
        self.db_name = db_name
        self.memory_size_mb = memory_scheme_size_mb
        self.schemes: SchemeTable = SchemeTable()  
    
    def add_scheme(self, scheme_name: str, key_type: type, vals_type: type, rewrite_keys: bool) -> None:
        self.schemes._append_scheme(scheme_name=scheme_name,
                                    scheme=Scheme(key_type=key_type,
                                           vals_type=vals_type,
                                           rewrite_keys=rewrite_keys,
                                           memory_scheme_size_mb=self.memory_size_mb))
    
    def insert_into_sheme(self, scheme_name: str, data: Data) -> None:
        if not scheme_name in self.schemes._schemes.keys():
            raise InvalidSchemeName
        
        self.schemes._schemes[scheme_name].append_data(data)
        
    def close(self) -> None:
        save(data_file_path=os.path.join('./', 'internal', f'{self.db_name}'))
    