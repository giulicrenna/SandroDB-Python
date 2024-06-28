
![SandroDB](https://raw.githubusercontent.com/giulicrenna/SandroDB-Python/main/static/icon.png)


## SandroDB

SandroDB is a lightweight, in-memory database designed for efficient data storage and retrieval. It features a privilege management system, user management, and support for custom data schemes. The database allows for a flexible structure, enabling users to define their own data types and memory constraints.

### Features

- **In-Memory Storage**: Fast and efficient data operations.
- **Custom Schemes**: Define your own data types and memory limits.
- **User Management**: Create, delete, and manage users.
- **Privilege Management**: Control user access with a detailed privilege system.
- **Persistence**: Save and load the database state to and from disk.

### Installation

Clone the repository and install the required dependencies:

```sh
git clone https://github.com/giulicrenna/SandroDB-Python.git
cd SandroDB-Python
pip install -r requirements.txt
```

### Usage

#### Creating a Database

```python
from sandrodb import Database, Data

# Initialize the database
db = Database(db_name="my_database", memory_scheme_size_mb=50, user="admin", password="admin_pass")

# Add a new scheme
db.add_scheme(scheme_name="users", key_type=str, vals_type=dict, rewrite_keys=False, scheme_size_mb=10)

# Insert data into the scheme
user_data = Data(key_name="user1", value={"name": "Alice", "age": 30})
db.insert_into_scheme(scheme_name="users", data=user_data)

# Retrieve data from the scheme
user_info = db.get_registry(scheme_name="users", key="user1")
print(user_info)

# Save the database state
db.close()
```

### API Overview

#### `Database`

- `__init__(self, db_name: str, memory_scheme_size_mb: int, user: str, password: str)`: Initialize the database.
- `add_scheme(self, scheme_name: str, key_type: type, vals_type: type, rewrite_keys: bool, scheme_size_mb: int)`: Add a new scheme.
- `insert_into_scheme(self, scheme_name: str, data: Data)`: Insert data into a scheme.
- `get_registry(self, scheme_name: str, key: any)`: Retrieve data from a scheme.
- `delete_scheme(self, scheme_name: str)`: Delete a scheme.
- `read_all_schemes(self)`: Read all schemes in the database.
- `add_user(self, user_name: str, password: str)`: Add a new user.
- `delete_user(self, user: User)`: Delete a user.
- `close(self)`: Save the database state.

### Contributing

We welcome contributions to SandroDB! Please fork the repository and submit pull requests.

### License

This project is licensed under the MIT License.

### Contact

For questions or comments, please reach out to [giulicrenna@gmail.com](mailto:giulicrenna@gmail.com) or [https://github.com/giulicrenna].

---

This README provides a brief overview of SandroDB and its features, along with a basic example of how to use it. For more detailed information, please refer to the documentation.
