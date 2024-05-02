from typing import List, Tuple
from src.user import User
from src.exceptions import *

class Privileges:
    def __init__(self) -> None:
        self.READ_SCHEME: bool = False
        self.WRITE_SCHEME: bool = False
        self.ADD_SCHEME: bool = False
        self.DEL_SCHEME: bool = False
        self.GET_ALL_SCHEMES: bool = False

        self.ADD_REGISTRY: bool = False
        self.DEL_REGISTRY: bool = False
        self.UPDATE_REGISTRY: bool = False

        self.ADD_USER: bool = False
        self.DEL_USER: bool = False
        self.UPDATE_USER: bool = False

        self.READ_ROLE: bool = False
        self.READ_PRIVILEGE: bool = False
        self.WRITE_PRIVILEGE: bool = False
        
    def make_root(self) -> None:
        for attr in vars(self):
            if isinstance(getattr(self, attr), bool):
                setattr(self, attr, True)
                
    def __str__(self) -> str:
        properties = vars(self)
        return "[USER PRIVILEGES] " + " ".join(f"{prop}:{value}" for prop, value in properties.items() if isinstance(value, bool))
            
"""
Each database scheme has it's own privileges scheme.
"""
class PrivilegesScheme:
    def __init__(self) -> None:
        self.privileges: List[Tuple[User, Privileges]] = []
        
    def __str__(self) -> str:
        return "[PRIVILEGES SCHEMA] " + " ".join(f"{user}:{privileges}" for user, privileges in self.privileges)
    
    def get_all_users(self) -> List[User]:
        return [user for user, _ in self.privileges]
    
    def add_privilege(self, user: User, privileges: Privileges) -> None:
        if user in self.get_all_users():
            raise UserPrivilegesAlreadySetted
        
        self.privileges.append((user, privileges))
        
    def get_privileges(self, user: User) -> Privileges:
        if user not in self.get_all_users():
            raise UserPrivilegesNotSetted
        
        for user_obj, privileges in self.privileges:
            if user_obj.name == user.name:
                return privileges
        
        return Privileges()
    