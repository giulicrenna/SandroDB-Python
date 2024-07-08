
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

### System Commands

1. **`exit`**
   - **Description**: Close database engine.
   - **Usage**: `exit`

2. **`clear`**
   - **Description**: Clear the screen.
   - **Usage**: `clear`

3. **`help`**
   - **Description**: Show help.
   - **Usage**: `help`

4. **`debug`**
   - **Description**: 
   - **Usage**: `debug`

### Database Commands

1. **`create_db`**
   - **Description**: Creates a new database.
   - **Arguments**:
     - `name` `<str>`: Name of the database.
   - **Usage**: `create_db [name]`

2. **`use_db`**
   - **Description**: Select database to use.
   - **Arguments**:
     - `name` `<str>`: Name of the database.
   - **Usage**: `use_db [name]`

3. **`show_databases`**
   - **Description**: Show available databases.
   - **Usage**: `show_databases`

4. **`exit_db`**
   - **Description**: Close the selected database.
   - **Arguments**:
     - `name` `<str>`: Name of the database.
   - **Usage**: `exit_db [name]`

### Scheme Commands

1. **`create_scheme`**
   - **Description**: Creates a new scheme.
   - **Arguments**:
     - `name` `<str>`: Name of the scheme.
     - `type1` `<type>`: First type.
     - `type2` `<type>`: Second type.
     - `overwrite registry` `<bool>`: Overwrite registry flag.
     - `size` `<int>`: Size of the scheme.
   - **Usage**: `create_scheme [name] [type1] [type2] [overwrite registry] [size]`

2. **`show_schemes`**
   - **Description**: Show all available schemes in selected database.
   - **Usage**: `show_schemes`

3. **`del_scheme`**
   - **Description**: Delete scheme.
   - **Arguments**:
     - `name` `<str>`: Name of the scheme.
   - **Usage**: `del_scheme [name]`

### Registry Commands

1. **`insert_into`**
   - **Description**: Inserts a new record into a scheme.
   - **Arguments**:
     - `scheme name` `<str>`: Name of the scheme.
     - `key` `<any>`: Key of the record.
     - `value` `<any>`: Value of the record.
   - **Usage**: `insert_into [scheme name] [key] [value]`

2. **`get_registry`**
   - **Description**: Gets a record from a scheme.
   - **Arguments**:
     - `scheme name` `<str>`: Name of the scheme.
     - `key` `<any>`: Key of the record.
   - **Usage**: `get_registry [scheme name] [key]`

3. **`get_all_registry`**
   - **Description**: Gets all records from a scheme.
   - **Arguments**:
     - `scheme name` `<str>`: Name of the scheme.
   - **Usage**: `get_all_registry [scheme name]`

4. **`del_registry`**
   - **Description**: Deletes a record from a scheme.
   - **Arguments**:
     - `scheme name` `<str>`: Name of the scheme.
     - `key` `<any>`: Key of the record.
   - **Usage**: `del_registry [scheme name] [key]`

5. **`update_registry`**
   - **Description**: Updates a record in a scheme.
   - **Arguments**:
     - `scheme name` `<str>`: Name of the scheme.
     - `key` `<any>`: Key of the record.
     - `value` `<any>`: New value of the record.
   - **Usage**: `update_registry [scheme name] [key] [value]`

### User Commands

1. **`login`**
   - **Description**: Login to the database.
   - **Arguments**:
     - `username` `<str>`: Username.
     - `password` `<str>`: Password.
   - **Usage**: `login [username] [password]`

2. **`logout`**
   - **Description**: Logout from the database.
   - **Usage**: `logout`

3. **`show_users`**
   - **Description**: Shows users in the selected database.
   - **Usage**: `show_users`

4. **`register`**
   - **Description**: Register a new user into the selected database.
   - **Arguments**:
     - `username` `<str>`: Username.
     - `password` `<str>`: Password.
   - **Usage**: `register [username] [password]`

5. **`del_user`**
   - **Description**: Delete user.
   - **Arguments**:
     - `username` `<str>`: Username.
   - **Usage**: `del_user [username]`

6. **`change_password`**
   - **Description**: Change user password.
   - **Arguments**:
     - `username` `<str>`: Username.
     - `new password` `<str>`: New password.
     - `old password` `<str>`: Old password.
   - **Usage**: `change_password [username] [new password] [old password]`

7. **`change_permission`**
   - **Description**: Change user permission.
   - **Arguments**:
     - `username` `<str>`: Username.
     - `permission` `<str>`: Permission type.
     - `value` `<bool>`: Permission value.
   - **Usage**: `change_permission [username] [permission] [value]`

8. **`show_permission`**
   - **Description**: Show user permissions.
   - **Usage**: `show_permission`


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
