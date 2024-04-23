from src.database import Database, Data

my_redis: Database = Database('my_db')

my_redis.add_scheme('users', str, str)

my_redis.insert_into_sheme('users', Data('hola', 'carola'))

my_redis.insert_into_sheme('users', Data('hola2', 'carola2'))

my_redis.close()