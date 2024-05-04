DEBUG: bool = True

class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class Logger:
    @staticmethod
    def print_log_error(log: str, instance: str) -> None:
        print(Color.RED + f'[ERROR] <{instance}>' + Color.END + f': {log}')

    @staticmethod
    def print_log_normal(log: str, instance: str) -> None:
        print(Color.GREEN + f'[SIGNAL] <{instance}>' + Color.END + f': {log}')

    @staticmethod
    def print_log_debug(log: str) -> None:
        if not DEBUG: return
        print(Color.PURPLE + f'[DEBUG]' + Color.END + f': {log}')
        
    @staticmethod
    def print_log_warning(log: str) -> None:
        print(Color.YELLOW + f'[WARNING]' + Color.END + f': {log}')
        
    @staticmethod
    def print_database_output(state: str, log: str) -> None:
        print(Color.BLUE + f'[DATABASE]' + Color.END + Color.GREEN + f' <{state}>' + Color.END + f': {log}')