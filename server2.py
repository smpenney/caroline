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


class AccioServer(Thread):
    def __init__(self, port, sel, dir) -> None:
        super().__init__(daemon=True)
        self.sel = selectors.DefaultSelector()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection_counter = 0
        self.port = port
        self.sel = sel
        self.dir = dir

    def run(self):

        self.server.bind((HOST, self.port))
        self.server.listen(10)

        sys.stdout.write(f'Server started on port {self.port}\n')

        while True:
            try:
                events = self.sel.select(timeout=None)
                for key, mask in events:
                    if key.data is None:
                        connection_counter += 1
                        threading.Thread(target=self.handshake, args=(
                            key.fileobj, connection_counter,)).start()
                    else:
                        threading.Thread(target=handle_connection, args=(
                            key, mask, connection_counter, dir,)).start()
                        self.sel.unregister(key.fileobj)
            except Exception as e:
                sys.stderr.write(f'ERROR: {e}\n')


    def handshake(self, inbound: socket.socket, id: int) -> None:
        conn, addr = inbound.accept()
        sys.stdout.write(
            f'New connection: {id} : {addr}... attempting handshake\n')
        try:
            shakes = 0
            while shakes < HANDSHAKES:
                conn.send(COMMAND)
                msg = conn.recv(PACKET_SIZE)
                print(f'RECV: {msg}')
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
            sys.stderr.write(f'ERROR: handshake failed for {addr}: {e}\n')
            return False


def signal_handler(signum: int, frame: any) -> None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)




def handle_connection(key: selectors.SelectorKey, mask: int, num: int, dir: str) -> None:
    size = 0
    conn = key.fileobj
    data = key.data

    with open(f'{dir}/{num}.file', 'wb') as f:
        f.write(b'ERROR')
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
    
    server = AccioServer(port, sel, dir).start()
    server.join()


if __name__ == '__main__':
    main()
