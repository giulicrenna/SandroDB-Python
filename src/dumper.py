import pickle
from src.database import Database

def save(data_file_path: str,
         database: Database) -> None:
    
    with open(data_file_path, 'wb') as db:
        pickle.dump(obj=database.get_data_schemes(),
                    file=db)
    
def load(data_file_path: str) -> Database:
    with open(data_file_path, 'rb') as db:
        return pickle.load(db)
    
        