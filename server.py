import socket
import sys
import threading

packet_size = 4096
host = '0.0.0.0'
server = socket.socket()
connection_counter = 0

try:
    port = int(sys.argv[1])
except:
    print('ERROR: No port specified')
    sys.exit(1)

server.bind((host, port))
server.listen()
print('Server started on port', port)


def handle_connection(conn: socket.socket, num: int):
    size = 0
    with conn:
        try:
            conn.send(b'accio\r\n')
            with open(f'{num}.file', 'wb') as f:
                while True:
                    data = conn.recv(packet_size)
                    print(data)
                    if not data:
                        break
                    f.write(data)
                    size += len(data)
        except Exception as e:
            print('Error: ', e)
    print(f'Worker thread finished, received {size}')


while True:
    try:
        conn, addr = server.accept()
        print(f'Connection: {conn}, {addr}')
        connection_counter += 1

        t = threading.Thread(target=handle_connection, args=(conn, connection_counter,))
        t.start()
        t.join()

    except KeyboardInterrupt:
        print('Shutting down')
        server.close()
        break
