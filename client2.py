import socket
import sys
import signal

PACKET_SIZE = 4096
TIMEOUT = 10
COMMAND = b'accio\r\n'
CONFIRMATION1 = b'confirm-accio\r\n'
CONFIRMATION2 = b'confirm-accio-again\r\n\r\n'
HANDSHAKES = 2


def signal_handler(signum: int, frame: any) -> None:
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\n')
    raise SystemExit(0)


def handshake(conn: socket.socket) -> bool:
    try:
        shakes = 0
        while shakes < HANDSHAKES:
            msg = conn.recv(PACKET_SIZE)
            print(f'RECV: {msg}')
            if msg == COMMAND and shakes == 0:
                shakes += 1
                conn.send(CONFIRMATION1)
            elif msg == COMMAND and shakes == 1:
                shakes += 1
                conn.send(CONFIRMATION2)
        return True
    except Exception as e:
        sys.stderr.write(f'ERROR: handshake failed for {conn}\n')
        return False


def send_file(host: str, port: int, file: str) -> None:
    # Create a socket to handle the file upload
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
        conn.setblocking(False)
        conn.settimeout(TIMEOUT)

        # Initiate TCP connection between client and server
        try:
            conn.connect((host, port))
            print("Connection established.")
        except:
            sys.stderr.write(f"ERROR: Failed to connect to {host}:{port}")
            raise SystemExit(1)

        # Receive accio commands
        if not handshake(conn):
            return
        
        print(f'SUCCESS: handshake complete for {host}:{port}')

        # Try to send file
        while True:
            print('nothing')
        # Terminate the connection
        try:
            conn.close()
            raise SystemExit(0)
        except Exception as e:
            sys.stderr.write(f"ERROR: Failed to close the connection: {e}")
            raise SystemExit(1)


def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate arguments exist
    if len(sys.argv) != 4:
        sys.stderr.write("Usage: python client.py host port filename")
        raise SystemExit(1)

    # Get host, port and file path from command line arguments
    host = sys.argv[1]
    port = int(sys.argv[2])
    file_name = sys.argv[3]

    # Validate port number
    if not (port >= 1 and port):
        sys.stderr.write(f"ERROR: Invalid port specified: {port}\n")
        raise SystemExit(1)

    send_file(host, port, file_name)


if __name__ == '__main__':
    main()