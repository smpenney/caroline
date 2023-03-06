import socket
import sys
import threading
import signal

TIMEOUT = 10
PACKET_SIZE = 4096
HOST = '0.0.0.0'


def signal_handler(signum, frame):
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\r\n')
    sys.exit(0)


def handle_connection(conn: socket.socket, addr: str, num: int):
    size = 0
    conn.setblocking(False)
    conn.settimeout(TIMEOUT)

    with conn:
        conn.send(b'accio\r\n')
        try:
            file = b''
            while True:
                data = conn.recv(PACKET_SIZE)
                if not data:
                    break
                file += data
                size += len(data)
        except Exception as e:
            sys.stderr.write(f'Error: {e}\r\n')

        with open(f'{num}.file', 'wb') as f:
                f.write(file)

    sys.stdout.write(f'Thread for file {num}: received {size} bytes from {addr}\r\n')

def listener(host, port):
    server = socket.socket()
    server.bind((HOST, port))
    server.listen()
    sys.stdout.write(f'Server started on port {port}\r\n')

    connection_counter = 0
    while True:
        try:
            conn, addr = server.accept()
            sys.stdout.write(f'Connection: {addr}\r\n')
            connection_counter += 1

            t = threading.Thread(target=handle_connection, args=(
                conn, addr, connection_counter,)).start()
            # t.join()

        except Exception as e:
            sys.stderr.write('ERROR: {e}\r\n')

def main():

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        port = int(sys.argv[1])
    except:
        sys.stderr.write('ERROR: No port specified\r\n')
        sys.exit(1)

    listener(HOST, port)


if __name__ == '__main__':
    main()
