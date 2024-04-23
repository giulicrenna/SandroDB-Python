from src.database import Database, Data
import atexit



my_redis: Database = Database('my_db')

try:
    my_redis.add_scheme('users', str, str, False, 2048)
except:
    pass

#####

from src.utils import getsize
from faker import Faker

f = Faker()

for _ in range(10000000):
    try:
        my_redis.insert_into_scheme('users', Data(f.name(), f.email()))
    except KeyboardInterrupt:
        break
    except Exception as e:
        break

######

print(my_redis.read_all_schemes())

def at_exit() -> None:
    print('Exiting...')
    my_redis.close()

atexit.register(at_exit)