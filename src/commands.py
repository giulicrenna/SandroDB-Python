from src.logger import Logger

class Commands:
    def __init__(self) -> None:
        # implemented
        self.EXIT: tuple[str, str] = ('exit', 'Close database engine.')
        # implemented
        self.CLEAR: tuple[str, str] = ('clear', 'Clear the screen.')
        # implemented
        self.HELP: tuple[str, str] = ('help', 'Show help.')
        # implemented
        self.DEBUG: tuple[str, str] = ('debug', '')

        # implemented
        self.CREATE_DB: tuple[str, str] = ('create_db', f'ARGS: [name]<str> - Creates a new database.')
        # implemented
        self.USE_DB: tuple[str, str] = ('use_db', 'ARGS: [name]<str> - Select database to use.')
        # implemented
        self.SHOW_DATABASES: tuple[str, str] = ('show_databases', 'ARGS: [name]<str> - Select available databases.')
        
        self.EXIT_DB: tuple[str, str] = ('exit_db', 'ARGS: [name]<str> - Close database.')
    
        # implemented
        self.CREATE_SCHEME: tuple[str, str] = ('create_scheme', 'ARGS: [name]<str> [type1]<type> [type2]<type> [overwrite registry]<bool> [size]<int>- Creates a new scheme.')
        # implemented
        self.SHOW_SCHEMES: tuple[str, str] = ('show_schemes', 'Show all available schemes in selected database.')
        # implemented
        self.DEL_SCHEME: tuple[str, str] = ('del_scheme', 'ARGS: [name]<str> - Delete scheme.')

        # implemented
        self.INSERT_INTO: tuple[str, str] = ('insert_into', 'ARGS: [scheme name]<str> [key]<any> [value]<any> - Inserts a new record into a scheme.>')
        # implemented
        self.GET_REGISTRY: tuple[str, str] = ('get_registry', 'ARGS: [scheme name]<str> [key]<any> - Gets a record from a scheme.')
        # implemented
        self.GET_ALL_REGISTRY: tuple[str, str] = ('get_all_registry', 'ARGS: [scheme name]<str> - Gets all records from a scheme.')
        
        self.DEL_REGISTRY: tuple[str, str] = ('del_registry', 'ARGS: [scheme name]<str> [key]<any> - Deletes a record from a scheme.')
        
        self.UPDATE_REGISTRY: tuple[str, str] = ('update_registry', 'ARGS: [scheme name]<str> [key]<any> [value]<any> - Updates a record in a scheme.')
    
        # implemented
        self.LOGIN: tuple[str, str] = ('login', 'ARGS: [username]<str> [password]<str> - Login to the database.')
        # implemented
        self.LOGOUT: tuple[str, str] = ('logout', 'Logout from the database.')
        
        self.SHOW_USERS: tuple[str, str] = ('show_users', 'Shows users in the selected database.')
        
        self.REGISTER: tuple[str, str] = ('register', 'ARGS: [username]<str> [password]<str> - Register a new user into selected database..')
        
        self.DEL_USER: tuple[str, str] = ('del_user', 'ARGS: [username]<str> - Delete user.')
        
        self.CHANGE_PASSWORD: tuple[str, str] = ('change_password', 'ARGS: [username]<str> [new password]<str> [old password]<str> - Change user password.')
        
        self.CHANGE_PERMISSION: tuple[str, str] = ('change_permission', 'ARGS: [username]<str> [permission]<str> [value]<bool> - Change user permission.')
        
        self.SHOW_PERMISSION: tuple[str, str] = ('show_permission', 'Show user permission.')

    def show_help(self) -> str:
        Logger.print_database_output("HELP", "Showing available commands.")
        help: str = '' 
        for cmd_name, cmd_desc in self.__dict__.values():
            comm: str = f"\t* {cmd_name} -> {cmd_desc}"
            help += comm
        
        return help