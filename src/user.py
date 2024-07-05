from src.exceptions import *
from typing import List
import hashlib

def calculate_sha256(string):
    sha256 = hashlib.sha256()
    sha256.update(string.encode())
    return sha256.hexdigest()

class User: 
    def __init__(self, name: str) -> None:
        self.name = name
        self.password = None
        
    def set_password(self, password: str) -> None:
        if self.password is not None:
            raise PasswordAlreadySetted
        
        self.password = calculate_sha256(password)

    def validate_password(self, password: str) -> bool:
        if self.password is None:
            raise PasswordNotSetted
        return self.password == calculate_sha256(password)

    def change_password(self, password: str, old_password: str) -> None:
        if self.password is None:
            raise PasswordNotSetted
        
        if self.validate_password(old_password):
            self.password = calculate_sha256(password)
    
    def __str__(self) -> str:
        return f"[USER]: name: {self.name} password: {self.password} "
    
class UserScheme:
    def __init__(self) -> None:
        root: User = User("root")
        root.set_password("root")
        
        self.users: List[User] = [root]
        
    def __str__(self) -> str:
        return f"[USER_SCHEME]: users: {self.users}"
    
    def get_all_users(self) -> List[User]:
        return self.users
    
    def get_all_users_names(self) -> List[str]:
        return [user.name for user in self.users]
    
    def get_user_by_password(self, password: str) -> User:
        for user in self.users:
            if user.password == calculate_sha256(password):
                return user
        
        return None
    
    def add_user(self, user: User) -> None:
        if user in self.users:
            raise UserAlreadyExists
        
        self.users.append(user)
        
    def remove_user(self, user: User) -> None:
        if user.name == "root":
            raise RootUserCannotBeRemoved
        
        if user not in self.users:
            raise UserDoesNotExist
        
        self.users.remove(user)
        
    def get_user(self, name: str, password: str) -> User:
        if name not in self.get_all_users_names():
            raise UserDoesNotExist
        
        for user in self.users:
            if user.name == name:
                if user.validate_password(password):
                    return user
                else:
                    raise InvalidPasswordException
                        
        return None