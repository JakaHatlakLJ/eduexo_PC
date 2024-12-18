import socket

# UDP setup (PC listening side)
UDP_IP = "0.0.0.0"  # Listen on all available interfaces
UDP_PORT = 5005      # Port number should match the sender's port

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print(f"Listening on {UDP_IP}:{UDP_PORT}...")

while True:
    data, addr = sock.recvfrom(1024)  # Buffer size of 1024 bytes
    decoded_data = data.decode('utf-8')

    if decoded_data.isdigit():
        print(f"Motor current position: {round(float(decoded_data) * 0.088, 2)} deg")#, from {addr}")
    else:
        print(decoded_data)
        break