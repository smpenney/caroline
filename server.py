import socket
import sys
import signal
import selectors
import types

TIMEOUT = 10
PACKET_SIZE = 32768
HOST = '0.0.0.0'
COMMAND = b'accio\r\n'
CONFIRMATION = b'confirm\r\n'
HANDSHAKES = 2

sel = selectors.DefaultSelector()


def signal_handler(signum: int, frame: any) -> None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)


def handshake(inbound: socket.socket, id: int) -> None:
    conn, addr = inbound.accept()
    sys.stdout.write(
        f'New connection: {id} : {addr}... attempting handshake\n')
    try:
        shakes = 0
        while shakes < HANDSHAKES:
            conn.sendall(COMMAND)
            msg = conn.recv(PACKET_SIZE)
            if msg == CONFIRMATION:
                shakes += 1
        sys.stderr.write(f'SUCCESS: handshake complete for {addr}\n')
        conn.setblocking(False)
        conn.settimeout(TIMEOUT)
        data = types.SimpleNamespace(addr=addr, num=id)
        # data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'', num=id)
        # events = selectors.EVENT_READ | selectors.EVENT_WRITE
        events = selectors.EVENT_READ
        sel.register(conn, events, data=data)
    except Exception as e:
        sys.stderr.write(f'ERROR: handshake failed for {addr}\n')
        return False


def handle_connection(key: selectors.SelectorKey, mask: int, num: int, dir: str) -> None:
    size = 0
    conn = key.fileobj
    data = key.data

    if mask & selectors.EVENT_READ:
        with conn:
            try:
                file = b''
                while True:
                    filedata = conn.recv(PACKET_SIZE)
                    if not filedata:
                        break
                    file += filedata
                    size += len(filedata)

                with open(f'{dir}/{num}.file', 'wb') as f:
                    f.write(file)
                sys.stdout.write(
                    f'Thread for file {num}: received {size} bytes from {data.addr}\n')
            except Exception as e:
                sys.stderr.write(f'Error: {e}\n')
                with open(f'{dir}/{num}.file', 'wb') as f:
                    f.write(b'ERROR')
        sel.unregister(conn)
        conn.close()
    # if mask & selectors.EVENT_WRITE:
    #     if data.outb:
    #         print(f'Echoing {data.outb} to {data.addr}')
    #         sent = conn.send(data.outb)
    #         data.outb = data.outb[sent:]


def listener(port: int, dir: str) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, port))
    server.listen(10)
    sys.stdout.write(f'Server started on port {port}\n')
    server.setblocking(False)
    sel.register(server, selectors.EVENT_READ, data=None)

    connection_counter = 0
    while True:
        try:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    connection_counter += 1
                    handshake(key.fileobj, connection_counter)
                else:
                    handle_connection(key, mask, connection_counter, dir)
        except Exception as e:
            sys.stderr.write(f'ERROR: {e}\n')


def main():

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        port = int(sys.argv[1])
    except:
        sys.stderr.write('ERROR: No port specified\n')
        raise SystemExit(1)

    # Validate port number
    if not (port >= 1 and port):
        sys.stderr.write(f"ERROR: Invalid port specified: {port}\n")
        raise SystemExit(1)

    try:
        dir = sys.argv[2]
    except:
        sys.stderr.write('ERROR: No directory specified\n')
        raise SystemExit(1)


    listener(port, dir)


if __name__ == '__main__':
    main()
