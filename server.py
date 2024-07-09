from src.core import Interpreter, InterpreterType, VirtualMemory
from typing import Dict, Any, Tuple
from src.logger import *
from uuid import uuid4
import selectors
import socket

sel = selectors.DefaultSelector()
virtual_memory: VirtualMemory = VirtualMemory()

# Diccionario para almacenar las conexiones activas
connections: Dict[int, socket.socket] = {}
# Diccionario para mapear comandos a sus respectivas conexiones
command_to_conn: Dict[str, Tuple[socket.socket, Interpreter]] = {}

def output_callback(output_data: str, conn_id: int) -> None:
    try:
        if conn_id in list(command_to_conn.keys()):
            conn = command_to_conn[conn_id]
            conn.sendall(output_data.encode())
            del(command_to_conn[conn_id])
    
    except OSError:
        connections[conn_id][0].close()
        del(connections[conn_id])
        
# Función para aceptar nuevas conexiones
def accept(sock: socket.socket, mask: Any) -> None:
    try:
        conn, addr = sock.accept()
        
        Logger.print_log_normal(f'Connection accepted from {addr}', 'accept')
        
        conn.setblocking(False)

        sel.register(conn, selectors.EVENT_READ, read)

        interpreter: Interpreter = Interpreter(type=InterpreterType.server,
                                            virtual_memory=virtual_memory,
                                            conn_id=conn.fileno())    

        connections[conn.fileno()] = (conn, interpreter)

        interpreter.set_output_callback(output_callback)

        interpreter.start()
    except Exception as e:
        Logger.print_log_error(str(e), 'accept')
        
# Función para manejar la lectura de datos de un cliente
def read(conn: socket.socket, mask: Any) -> None:
    try:
        data = conn.recv(1024)  # Tamaño del buffer de lectura
        if data:
            command = data.decode()
            command_to_conn[conn.fileno()] = conn
            
            Logger.print_log_debug(f'[{conn}] {command}')
            
            conn_interpreter: Interpreter = connections[conn.fileno()][1]
            conn_interpreter.add_command_task(command=command.strip())
        else:
            Logger.print_log_warning(f'Closing connection to {conn}')
            sel.unregister(conn)
            #conn.close()
            del(connections[conn.fileno()])
            
    except Exception as e:
        Logger.print_log_error(str(e), 'read')
        sel.unregister(conn)
        del(connections[conn.fileno()])

# Configurar el servidor
host, port = '192.168.0.107', 65432
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen()
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)

Logger.print_log_normal(f'Server started at {host}:{port}', 'server')

try:
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
except KeyboardInterrupt:
    print('Servidor detenido')
except KeyError:
    pass
finally:
    sel.close()
