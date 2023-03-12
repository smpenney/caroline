import socket
import sys
import signal
import threading
import selectors
import types

TIMEOUT = 10
PACKET_SIZE = 32768
HOST = '0.0.0.0'
COMMAND = b'accio\r\n'
CONFIRMATION1 = b'confirm-accio\r\n'
CONFIRMATION2 = b'confirm-accio-again\r\n\r\n'
HANDSHAKES = 2


class AccioServer(threading.Thread):
    def __init__(self, port: int, dir: str, sel: selectors.DefaultSelector) -> None:
        super().__init__(daemon=True)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection_counter = 0
        self.sel = sel
        self.port = port
        self.dir = dir

    def run(self) -> None:
        self.server.bind((HOST, self.port))
        self.server.listen()
        sys.stdout.write(f'Server started on port {self.port}\n')

        while True:
            try:
                conn, addr = self.server.accept()
                sys.stdout.write(f'ACCEPT: {addr}\n')
                self.connection_counter += 1
                self.handshake(conn, addr, self.connection_counter)
            except Exception as e:
                sys.stderr.write(f'ERROR: accepting {addr}: {e}\n')

    def handshake(self, conn: socket.socket, addr: str, id: int) -> None:
        sys.stdout.write(
            f'New connection: {id} : {addr}... attempting handshake\n')

        with open(f'{self.dir}/{self.connection_counter}.file', 'wb') as f:
            f.write(b'ERROR')

        conn.settimeout(TIMEOUT)
        try:
            shakes = 0
            while shakes < HANDSHAKES:
                conn.send(COMMAND)
                msg = conn.recv(PACKET_SIZE)
                sys.stdout.write(f'RECV: {msg}\n')
                if msg == CONFIRMATION1 and shakes == 0:
                    shakes += 1
                if msg == CONFIRMATION2 and shakes == 1:
                    shakes += 1
            sys.stderr.write(f'SUCCESS: handshake complete for {addr}\n')
            conn.settimeout(TIMEOUT)
            data = types.SimpleNamespace(addr=addr, num=id)
            events = selectors.EVENT_READ
            self.sel.register(conn, events, data=data)
        except Exception as e:
            sys.stderr.write(f'ERROR in handshake: failed for {addr}: {e}\n')


class AccioTransfer(threading.Thread):
    def __init__(self, sel, dir):
        super().__init__(daemon=True)
        self.dir = dir
        self.sel = sel

    def handle_connection(self, key: selectors.SelectorKey) -> None:
        size = 0
        conn = key.fileobj
        data = key.data

        with conn:
            try:
                file = b''
                while True:
                    filedata = conn.recv(PACKET_SIZE)
                    if not filedata:
                        break
                    file += filedata
                    size += len(filedata)

                with open(f'{self.dir}/{data.num}.file', 'wb') as f:
                    f.write(file)
                sys.stdout.write(
                    f'Thread for file {data.num}: received {size} bytes from {data.addr}\n')
            except Exception as e:
                sys.stderr.write(f'ERROR in handle_connection: {e}\n')

    def run(self):
        while True:
            events = self.sel.select(timeout=None)
            for key, mask in events:
                if mask & selectors.EVENT_READ:
                    self.handle_connection(key)
                    self.sel.unregister(key.fileobj)


def signal_handler(signum: int, frame: any) -> None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)


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

    sel = selectors.DefaultSelector()

    AccioTransfer(sel, dir).start()
    server = AccioServer(port, dir, sel)
    server.start()
    server.join()


if __name__ == '__main__':
    main()
