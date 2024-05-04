import pickle
import os

class Database:
    def __init__(self) -> None:
        pass

def save(data_file_path: str,
         database: Database) -> None:
 
    with open(data_file_path, 'wb') as db:
        pickle.dump(obj=database,
                    file=db)
        
def save_generic(data_file_path: str,
         object: Database) -> None:
 
    with open(data_file_path, 'wb') as obj:
        pickle.dump(obj=object,
                    file=obj)
    
def load(data_file_path: str) -> Database | dict:
    if os.path.isfile(data_file_path):
        with open(data_file_path, 'rb') as db:
            return pickle.load(db)
    