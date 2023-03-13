import socket
import sys
import signal
import threading
import os

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

        signal.signal(signal.SIGINT, self.__signal_handler)
        signal.signal(signal.SIGQUIT, self.__signal_handler)
        signal.signal(signal.SIGTERM, self.__signal_handler)

    def __close(self, signame=None):
        if signame:
            sys.stdout.write(f'SERVER: shutting down after signal {signame}\n')
        # self.server.shutdown(socket.SHUT_RDWR)
        self.server.close()
        raise SystemExit(0)

    def __signal_handler(self, sigid: int, frame: any) -> None:
        signame = signal.Signals(sigid).name
        sys.stderr.write(f'SIGNAL: {signame} ({sigid})\n')
        self.__close(signame)

    def __generate_error(self):
        with open(f'{self.dir}/{self.id}.file', 'wb') as f:
            f.write(b'ERROR')


    def run(self) -> None:
        self.server.bind((HOST, self.port))
        self.server.listen()
        sys.stdout.write(f'SERVER: pid {os.getpid()} listening on port {self.port}\n')

        while True:
            try:
                conn, addr = self.server.accept()
                self.id += 1
                sys.stdout.write(f'ACCEPT {self.id}: {addr}\n')
                self.__generate_error()
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

    def __generate_error(self):
        with open(f'{self.dir}/{self.id}.file', 'wb') as f:
            f.write(b'ERROR')

    def __handshake(self) -> bool:
        sys.stderr.write(
            f'THREAD {self.id}: Start handshake: {self.addr}\n')
        self.__generate_error()
        self.conn.settimeout(TIMEOUT)
        try:
            shakes = 0
            while shakes < HANDSHAKES:
                self.conn.send(COMMAND)
                if shakes == 0:
                    msg_buffer = b''
                    len_remains = len(CONFIRMATION1)
                    while True:
                        msg = self.conn.recv(len_remains)
                        msg_buffer += msg
                        print(f'msg: {msg}, buffer: {msg_buffer}')
                        if msg_buffer == CONFIRMATION1:
                            shakes += 1
                            break
                        else:
                            len_remains -= len(msg)
                elif shakes == 1:
                    msg_buffer = b''
                    len_remains = len(CONFIRMATION2)
                    while True:
                        msg = self.conn.recv(len_remains)
                        msg_buffer += msg
                        print(f'msg: {msg}, buffer: {msg_buffer}')
                        if msg_buffer == CONFIRMATION2:
                            shakes += 1
                            break
                        else:
                            len_remains -= len(msg)
            sys.stderr.write(f'THREAD {self.id}: SUCCESS handshake for {self.addr}\n')
            return True
        except Exception as e:
            sys.stderr.write(f'THREAD {self.id}: ERROR handshake for {self.addr}: {e}\n')
            return False

    def __handle_connection(self) -> None:
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
                    sys.stderr.write(f'THREAD {self.id}: no data received, writing ERROR file\n')
                    self.__generate_error()
            except Exception as e:
                sys.stderr.write(f'THREAD {self.id}: ERROR in __handle_connection: {e}\n')
                self.__generate_error()


    def run(self):
        if self.__handshake():
            self.__handle_connection()


def main():

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
