import selectors
import socket

sel = selectors.DefaultSelector()

# Función para aceptar nuevas conexiones
def accept(sock, mask):
    conn, addr = sock.accept()
    print('Aceptada conexión de', addr)
    conn.setblocking(False)
    sel.register(conn, selectors.EVENT_READ, read)

# Función para manejar la lectura de datos de un cliente
def read(conn, mask):
    data = conn.recv(1024)  # Tamaño del buffer de lectura
    if data:
        print('Recibido:', repr(data), 'de', conn)
        conn.sendall(data)  # Echo de vuelta al cliente
    else:
        print('Cerrando conexión a', conn)
        sel.unregister(conn)
        conn.close()

# Configurar el servidor
host, port = 'localhost', 65432
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((host, port))
sock.listen()
sock.setblocking(False)
sel.register(sock, selectors.EVENT_READ, accept)

print('Servidor iniciado en', (host, port))

try:
    while True:
        events = sel.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
except KeyboardInterrupt:
    print('Servidor detenido')
finally:
    sel.close()
