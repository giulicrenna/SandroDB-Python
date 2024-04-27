from typing import List

types: dict = {
    'int': int,
    'float': float,
    'str': str,
    'bool': bool,
    'list': list,
    'dict': dict,
    'tuple': tuple,
    'set': set,
    'frozenset': frozenset,
    'None': None
}

booleans: dict = {
    'True': True,
    'False': False
}

class Int:
    def __init__(self, value: int) -> None:
        if type(value) != int: raise Exception

        self.value: int = value
    
    def update_value(self, new_value: int) -> None:
        self.value = new_value
        
    def get_value(self) -> int:
        return self.value
    
class String:
    def __init__(self, value: int) -> None:
        if type(value) != str: raise Exception

        self.value: str = value
    
    def update_value(self, new_value: int) -> None:
        self.value = new_value
        
    def get_value(self) -> str:
        return self.value
    
class Array:
    def __init__(self, value: list, typo: any, maxsize: int = 1e6) -> None:
        if type(value) != list: raise Exception
        
        if len(value) == 0:
            self.value: List[typo] = value
        else:
            if not all([type(inside_val) for inside_val in value]):
                raise Exception
            
            if len(value) > maxsize:
                raise Exception
            
            self.value: List[typo] = value