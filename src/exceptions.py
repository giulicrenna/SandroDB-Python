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
        
class PasswordAlreadySetted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class PasswordNotSetted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class UserPrivilegesAlreadySetted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UserPrivilegesNotSetted(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidPasswordException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UserAlreadyExists(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class UserDoesNotExist(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class RootUserCannotBeRemoved(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidUserException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class NotEnoughPrivileges(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class InvalidKeyType(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class KeyNotFound(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class DatabaseAlreadyThere(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class DatabaseDoesNotExist(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        
class DatabaseDoNotSelected(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)