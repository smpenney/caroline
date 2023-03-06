import socket
import sys

PACKET_SIZE = 4096
TIMEOUT = 10
COMMAND = b'accio\r\n'
#CONFIRMATION = b'confirm\r\n'

# Validate arguments exist
if len(sys.argv) != 4:
    sys.stderr.write("Usage: python client.py host port filename")
    sys.exit(1)


# Get host, port and file path from command line arguments
host = sys.argv[1]
port = int(sys.argv[2])
file_name = sys.argv[3]

# Validate port number
if not port >= 1 and port:
    sys.stderr.write(f"ERROR: Invalid {port}")
    sys.exit(1)


# Create a socket to handle the file upload
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setblocking(False)
    s.settimeout(TIMEOUT)

    #Initiate TCP connection between client and server
    try:
        s.connect((host, int(port)))
        print("Connection established.")
    except:
        sys.stderr.write(f"ERROR: Failed to connect to {host}:{port}")
        sys.exit(1)

    #Receive accio commands
    try:
        msg = s.recv(PACKET_SIZE)
        print(f'RECV: {msg}')
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
        sys.stderr.write(f"ERROR: Failed to receive command from {host}:{port}\n")
        sys.exit(1)

    #Try to send file
    try:
        sent_size = 0
        with open(file_name, 'rb') as f:
            chunk = f.read(PACKET_SIZE)
            while chunk:
                s.send(chunk)
                sent_size += len(chunk)
                chunk = f.read(PACKET_SIZE)
        print(f'Sent: {sent_size}')            

        if sent_size == 0:
            raise Exception("Error: Failed to send data")
    except:
        sys.stderr.write(f"ERROR: Failed to send file to {host}:{port}")
        sys.exit(1)

    #Terminate the connection
    try:
        s.close()
        sys.exit(0)
    except Exception as e:
        sys.stderr.write(f"ERROR: Failed to close the connection: {e}")
        sys.exit(1)
