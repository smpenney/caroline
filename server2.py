import socket
import sys
import signal
import threading

TIMEOUT = 10
PACKET_SIZE = 524288
# PACKET_SIZE = 8192    # Testing slow transfers to enable multiple clients in parallel
HOST = '0.0.0.0'
COMMAND = b'accio\r\n'
CONFIRMATION1 = b'confirm-accio\r\n'
CONFIRMATION2 = b'confirm-accio-again\r\n\r\n'
HANDSHAKES = 2


class AccioServer(threading.Thread):
    def __init__(self, port: int, dir: str) -> None:
        super().__init__(daemon=True)
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.id = 0
        self.port = port
        self.dir = dir

    def generate_error(self):
        with open(f'{self.dir}/{self.id}.file', 'wb') as f:
            f.write(b'ERROR')


    def run(self) -> None:
        self.server.bind((HOST, self.port))
        self.server.listen()
        sys.stdout.write(f'Server started on port {self.port}\n')

        while True:
            try:
                conn, addr = self.server.accept()
                self.id += 1
                sys.stdout.write(f'ACCEPT {self.id}: {addr}\n')
                self.generate_error()
                AccioTransfer(conn, addr, self.id, self.dir).start()
            except Exception as e:
                sys.stderr.write(f'ERROR: accepting {addr}: {e}\n')



class AccioTransfer(threading.Thread):
    def __init__(self, conn, addr, id, dir):
        super().__init__(daemon=True)
        self.dir = dir
        self.id = id
        self.conn = conn
        self.addr = addr

    def generate_error(self):
        with open(f'{self.dir}/{self.id}.file', 'wb') as f:
            f.write(b'ERROR')

    def handshake(self) -> bool:
        sys.stdout.write(
            f'THREAD {self.id}: Start handshake: {self.addr}\n')
        self.generate_error()
        self.conn.settimeout(TIMEOUT)
        try:
            shakes = 0
            while shakes < HANDSHAKES:
                self.conn.send(COMMAND)
                if shakes == 0:
                    msg = self.conn.recv(len(CONFIRMATION1))
                    if msg == CONFIRMATION1:
                        shakes += 1
                elif shakes == 1:
                    msg = self.conn.recv(len(CONFIRMATION2))
                    if msg == CONFIRMATION2:
                        shakes += 1
            sys.stdout.write(f'THREAD {self.id}: SUCCESS handshake for {self.addr}\n')
            return True
        except Exception as e:
            sys.stderr.write(f'THREAD {self.id}: ERROR handshake for {self.addr}: {e}\n')
            return False

    def handle_connection(self) -> None:
        size = 0
        with self.conn:
            try:
                file = b''
                while True:
                    filedata = self.conn.recv(PACKET_SIZE)
                    if not filedata:
                        break
                    file += filedata
                    size += len(filedata)

                with open(f'{self.dir}/{self.id}.file', 'wb') as f:
                    f.write(file)
                sys.stdout.write(
                    f'THREAD {self.id}: received {size} bytes from {self.addr}\n')
                if size == 0:
                    sys.stderr.write(f'THREAD {self.id}: writing ERROR file - no data reeived!\n')
                    self.generate_error()
            except Exception as e:
                sys.stderr.write(f'THREAD {self.id}: ERROR in handle_connection: {e}\n')
                self.generate_error()


    def run(self):
        if self.handshake():
            self.handle_connection()


def signal_handler(sigid: int, frame: any) -> None:
    signame = signal.Signals(sigid).name
    sys.stderr.write(f'SIGNAL: {signame} ({sigid})\n')
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

    # Validate port idber
    if not (port >= 1 and port):
        sys.stderr.write(f"ERROR: Invalid port specified: {port}\n")
        raise SystemExit(1)

    try:
        dir = sys.argv[2]
    except:
        sys.stderr.write('ERROR: No directory specified\n')
        raise SystemExit(1)

    server = AccioServer(port, dir)
    server.start()
    server.join()


if __name__ == '__main__':
    main()
