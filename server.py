# Criar o servidor TCP e atender clientes

import socket

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen()

print(f"Servidor iniciado na porta {PORT}")

while True:
    conn, addr = server.accept()

    print(f"Cliente conectado: {addr}")

    conn.sendall(b"Conexao estabelecida!\n")

    conn.close()