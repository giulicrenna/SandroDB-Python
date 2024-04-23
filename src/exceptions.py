class InvalidTypeException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidArraySize(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidInnerType(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class SchemeAlreadyThere(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidDataTypeException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class SchemeReachedMaxSize(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidSchemeName(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        