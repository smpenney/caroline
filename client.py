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
        signal.raise_signal(signal.SIGQUIT)

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
            sys.exit(1)

        # Receive accio commands
        try:
            while True:
                msg = s.recv(PACKET_SIZE)
                print(f'RECV: {msg}')
                if msg == COMMAND:
                    s.sendall(CONFIRMATION)
                else:
                    break

            # while True:
            #     msg = s.recv(len(COMMAND))
            #     if msg == COMMAND:
            #         break
            #     print('Received from Server A: ', msg.decode())
            #     s.send('confirm-accio\r\n'.encode())
            #     while True:
            #         msg_2 = s.recv(10000)
            #         if msg_2 == COMMAND:
            #             break
            #         print('Received from Server B: ', msg_2.decode())
            #         s.send('confirm-accio-again\r\n\r\n'.encode())
        except:
            sys.stderr.write(f"ERROR: Failed to receive data from {host}:{port}\n")
            sys.exit(1)

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
            sys.exit(0)
        except Exception as e:
            sys.stderr.write(f"ERROR: Failed to close the connection: {e}")
            sys.exit(1)


if __name__ == '__main__':
    main()