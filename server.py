import socket
import sys
import threading

packet_size = 4096
host = '0.0.0.0'
server = socket.socket()
connection_counter = 0
TIMEOUT = 10

try:
    port = int(sys.argv[1])
except:
    sys.stderr.write('ERROR: No port specified\r\n')
    sys.exit(1)

server.bind((host, port))
server.listen()
sys.stdout.write(f'Server started on port {port}\r\n')


def handle_connection(conn: socket.socket, addr: str, num: int):
    size = 0
    conn.setblocking(False)
    conn.settimeout(TIMEOUT)

    with conn:
        conn.send(b'accio\r\n')
        try:
            file = b''
            while True:
                data = conn.recv(packet_size)
                if not data:
                    break
                file += data
                size += len(data)

            with open(f'{num}.file', 'wb') as f:
                f.write(file)

        except Exception as e:
            sys.stderr.write(f'Error: {e}\r\n')
    sys.stdout.write(f'Thread {num}, received {size} from {addr}\r\n')


while True:
    try:
        conn, addr = server.accept()
        sys.stdout.write(f'Connection: {addr}\r\n')
        connection_counter += 1

        t = threading.Thread(target=handle_connection, args=(conn, addr, connection_counter,)).start()
        # t.start()
        # t.join()

    except KeyboardInterrupt:
        sys.stdout.write('Shutting down\r\n')
        server.close()
        break
