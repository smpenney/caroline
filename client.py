import socket
import sys
import signal

PACKET_SIZE = 4096
TIMEOUT = 10
COMMAND = b'accio\r\n'
CONFIRMATION = b'confirm\r\n'


def signal_handler(signum, frame):
    signame = signal.Signals(signum).name
    sys.stderr.write(f'SIGNAL: {signame} ({signum})\r\n')
    raise SystemExit(0)


def handshake(conn):
    shakes = 0
    while shakes < 2:
        msg = conn.recv(PACKET_SIZE)
        print(f'RECV: {msg}')
        if msg == COMMAND:
            shakes += 1
            conn.sendall(CONFIRMATION)

def send_file(host, port, file):
          

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGQUIT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    # Validate arguments exist
    if len(sys.argv) != 4:
        sys.stderr.write("Usage: python client.py host port filename")
        sys.exit(1)


    # Get host, port and file path from command line arguments
    host = sys.argv[1]
    port = int(sys.argv[2])
    file_name = sys.argv[3]

    # Validate port number
    if not (port >= 1 and port):
        sys.stderr.write(f"ERROR: Invalid port specified: {port}\n")
        raise SystemExit(1)

    # Create a socket to handle the file upload
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setblocking(False)
        s.settimeout(TIMEOUT)

        # Initiate TCP connection between client and server
        try:
            s.connect((host, int(port)))
            print("Connection established.")
        except:
            sys.stderr.write(f"ERROR: Failed to connect to {host}:{port}")
            raise SystemExit(1)

        # Receive accio commands
        handshake(s)

        # Try to send file
        try:
            with open(file_name, 'rb') as f:
                chunk = f.read()
                s.sendall(chunk)
            print(f'Sent: {len(chunk)}')

            if len(chunk) == 0:
                raise Exception("Error: Failed to send data")
        except:
            sys.stderr.write(f"ERROR: Failed to send file to {host}:{port}")
            sys.exit(1)

        # Terminate the connection
        try:
            s.close()
            raise SystemExit(0)
        except Exception as e:
            sys.stderr.write(f"ERROR: Failed to close the connection: {e}")
            raise SystemExit(1)


if __name__ == '__main__':
    main()