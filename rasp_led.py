import socket
from gpiozero import LED

# 1. Setup your external LED pins (Change numbers to match your GPIO wiring)
led1 = LED(17)
led2 = LED(27)

# 2. Setup the Network Server
# Use '0.0.0.0' to listen to any device on your local Wi-Fi network
HOST = '0.0.0.0'  
PORT = 65432      # Match this port number on your desktop script

print("Initializing local network server...")
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    
    # Get the Pi's actual IP address to display to the user
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server is RUNNING! Raspberry Pi IP Address: {local_ip}")
    print(f"Waiting for your desktop to connect on port {PORT}...\n")

    try:
        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"Connected successfully by desktop at: {addr}")
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break # Desktop disconnected
                    
                    # Convert raw bytes back into a text command
                    command = data.decode('utf-8').strip()
                    print(f"Received number/command from desktop: {command}")

                    # 3. Control your external LEDs based on the desktop's choice
                    if command == '1':
                        led1.on()
                        led2.off()
                    elif command == '2':
                        led1.off()
                        led2.on()
                    elif command == '0':
                        led1.off()
                        led2.off()
                        
    except KeyboardInterrupt:
        print("\nShutting down server. Turning off LEDs.")
    finally:
        led1.off()
        led2.off()
