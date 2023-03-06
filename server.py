import socket
import sys
import threading
import signal

TIMEOUT = 10
PACKET_SIZE = 4096
HOST = '0.0.0.0'
COMMAND = b'accio\r\n'
CONFIRMATION = b'confirm\r\n'
HANDSHAKES = 2

def signal_handler(signum: int, frame: any) ->None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)

def handshake(conn: socket.socket, addr: str) -> bool:
    try:
        shakes = 0
        while shakes < HANDSHAKES:
            conn.sendall(COMMAND)
            msg = conn.recv(PACKET_SIZE)
            print(f'RECV: {msg}')
            if msg == CONFIRMATION:
                shakes += 1
        return True
    except Exception as e:
        sys.stderr.write(f'ERROR: handshake failed for {addr}\n')
        return False

def handle_connection(conn: socket.socket, addr: str, num: int, dir: str) -> None:
    size = 0
    conn.setblocking(False)
    conn.settimeout(TIMEOUT)

    if not handshake(conn, addr):
        return

    with conn:
        try:
            file = b''
            while True:
                data = conn.recv(PACKET_SIZE)
                if not data:
                    break
                file += data
                size += len(data)
            
            with open(f'{dir}/{num}.file', 'wb') as f:
                f.write(file)

        except Exception as e:
            sys.stderr.write(f'Error: {e}\n')


    sys.stdout.write(f'Thread for file {num}: received {size} bytes from {addr}\n')

def listener(port: int, dir: str) -> None:
    server = socket.socket()
    server.bind((HOST, port))
    server.listen()
    sys.stdout.write(f'Server started on port {port}\n')

    connection_counter = 0
    while True:
        try:
            conn, addr = server.accept()
            sys.stdout.write(f'Connection: {addr}\n')
            connection_counter += 1

            t = threading.Thread(target=handle_connection, args=(
                conn, addr, connection_counter, dir,)).start()
            # t.join()

        except Exception as e:
            sys.stderr.write('ERROR: {e}\n')

def main():

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        port = int(sys.argv[1])
    except:
        sys.stderr.write('ERROR: No port specified\n')
        raise SystemExit(1)

    try:
        dir = sys.argv[2]
    except:
        sys.stderr.write('ERROR: No directory specified\n')


    listener(port, dir)


if __name__ == '__main__':
    main()
