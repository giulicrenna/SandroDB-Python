from src.logger import Logger

class Commands:
    def __init__(self) -> None:
        self.EXIT: tuple[str, str] = ('exit', 'Close database engine.')
        self.CLEAR: tuple[str, str] = ('clear', 'Clear the screen.')
        self.HELP: tuple[str, str] = ('help', 'Show help.')
        self.DEBUG: tuple[str, str] = ('debug', '')

        self.CREATE_DB: tuple[str, str] = ('create_db', f'ARGS: [name]<str> [size]<int> - Creates a new database.')
        self.USE_DB: tuple[str, str] = ('use_db', 'ARGS: [name]<str> - Select database to use.')
        self.SHOW_DATABASES: tuple[str, str] = ('show_databases', 'ARGS: [name]<str> - Select available databases.')
        self.EXIT_DB: tuple[str, str] = ('exit_db', 'ARGS: [name]<str> - Close database.')
    
        self.CREATE_SCHEME: tuple[str, str] = ('create_scheme', 'ARGS: [name]<str> [type1]<type> [type2]<type> [overwrite registry]<bool> - Creates a new scheme.')
        self.SHOW_SCHEMES: tuple[str, str] = ('show_schemes', 'Show all available schemes in selected database.')
        self.DEL_SCHEME: tuple[str, str] = ('del_scheme', 'ARGS: [name]<str> - Delete scheme.')
        self.SHOW_ALL_SCHEMES: tuple[str, str] = ('show_all_schemes', 'Shows all available schemes in selected database.')

        self.INSERT_INTO: tuple[str, str] = ('insert_into', 'ARGS: [scheme name]<str> [key]<any> [value]<any> - Inserts a new record into a scheme.>')
        self.GET_REGISTRY: tuple[str, str] = ('get_registry', 'ARGS: [scheme name]<str> [key]<any> - Gets a record from a scheme.')
        self.GET_ALL_REGISTRY: tuple[str, str] = ('get_all_registry', 'ARGS: [scheme name]<str> - Gets all records from a scheme.')
        self.DEL_REGISTRY: tuple[str, str] = ('del_registry', 'ARGS: [scheme name]<str> [key]<any> - Deletes a record from a scheme.')
        self.UPDATE_REGISTRY: tuple[str, str] = ('update_registry', 'ARGS: [scheme name]<str> [key]<any> [value]<any> - Updates a record in a scheme.')
    
        self.LOGIN: tuple[str, str] = ('login', 'ARGS: [username]<str> [password]<str> - Login to the database.')
        self.LOGOUT: tuple[str, str] = ('logout', 'Logout from the database.')
        self.SHOW_USERS: tuple[str, str] = ('show_users', 'Shows users in the selected database.')
        self.REGISTER: tuple[str, str] = ('register', 'ARGS: [username]<str> [password]<str> - Register a new user into selected database..')
        self.DEL_USER: tuple[str, str] = ('del_user', 'ARGS: [username]<str> - Delete user.')
        self.CHANGE_PASSWORD: tuple[str, str] = ('change_password', 'ARGS: [username]<str> [new password]<str> [old password]<str> - Change user password.')
        
        self.CHANGE_PERMISSION: tuple[str, str] = ('change_permission', 'ARGS: [username]<str> [permission]<str> [value]<bool> - Change user permission.')
        
    def show_help(self) -> None:
        Logger.print_database_output("HELP", "Showing available commands.")
        for cmd_name, cmd_desc in self.__dict__.values():
            print(f"\t* {cmd_name} -> {cmd_desc}")
        