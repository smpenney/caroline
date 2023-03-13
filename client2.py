import socket
import sys
import signal
import time
import threading

TIMEOUT = 100
COMMAND = b'accio\r\n'
CONFIRMATION1 = b'confirm-accio\r\n'
CONFIRMATION2 = b'confirm-accio-again\r\n\r\n'
HANDSHAKES = 2


class AccioClientTransfer(threading.Thread):
    def __init__(self, host, port, id, file):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.id = id
        self.file = file

    def __handshake(self) -> bool:
        try:
            shakes = 0
            while shakes < HANDSHAKES:
                msg = self.conn.recv(len(COMMAND))
                print(f'RECV: {msg}')
                if msg == COMMAND and shakes == 0:
                    shakes += 1
                    self.conn.send(CONFIRMATION1)
                elif msg == COMMAND and shakes == 1:
                    shakes += 1
                    self.conn.sendall(CONFIRMATION2)
            sys.stdout.write(
                f'SUCCESS: handshake complete for {self.host}:{self.port}\n')
            return True
        except Exception as e:
            sys.stderr.write(f'ERROR: handshake failed for {self.conn}\n')
            return False

    def __test_timeout(self):
        time.sleep(TIMEOUT + 5)

    def __test_nodata(self):
        pass

    def __test_send_file(self):
        try:
            # Try to send file
            with open(self.file, 'rb') as f:
                chunk = f.read()
                self.conn.sendall(chunk)
            print(f'Sent: {len(chunk)}')

            if len(chunk) == 0:
                raise Exception("Error: Failed to send data")
            
        except Exception as e:
            sys.stderr.write(f"ERROR: {e}\n")
            sys.stderr.write(
                f"ERROR: Failed to send file to {self.host}:{self.port}\n")
            raise SystemExit(1)



    def __send_file(self) -> None:
        # Create a socket to handle the file upload
        with self.conn:

            action = self.id % 3
            match action:
                case 0: 
                    self.__test_send_file()     # send an actual file
                case 1:
                    self.__test_timeout()       # TIMEOUT testing
                case 2:
                    self.__test_nodata()        # drop connection test

            # Terminate the connection
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
                self.conn.close()
                raise SystemExit(0)
            except Exception as e:
                sys.stderr.write(
                    f"ERROR: Failed to close the connection: {e}\n")
                raise SystemExit(1)

    def run(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn.settimeout(TIMEOUT)
        # Initiate TCP connection between client and server
        try:
            self.conn.connect((self.host, self.port))
            sys.stdout.write("Connection established.\n")
            if self.__handshake():
                self.__send_file()
        except Exception as e:
            sys.stderr.write(
                f"ERROR: Failed to connect to {self.host}:{self.port}\n: {e}")
            raise SystemExit(1)


def signal_handler(signum: int, frame: any) -> None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate arguments exist
    if len(sys.argv) != 5:
        sys.stderr.write(
            "Usage: python client.py host port num_threads filename")
        raise SystemExit(1)

    # Get host, port and file path from command line arguments
    host = sys.argv[1]
    port = int(sys.argv[2])
    threads = int(sys.argv[3])
    file = sys.argv[4]

    # Validate port number
    if not (port >= 1 and port):
        sys.stderr.write(f"ERROR: Invalid port specified: {port}\n")
        raise SystemExit(1)

    clients = []
    for i in range(0, threads):
        client = AccioClientTransfer(host, port, i, file)
        client.start()
        clients.append(client)
    print(clients)
    for i in clients:
        i.join()




if __name__ == '__main__':
    main()
