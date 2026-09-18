import socket
import sys

# 1. Enter your Raspberry Pi's local network IP address here
# (You will see this printed on the Pi's screen when you run the Pi script)
PI_IP_ADDRESS = '192.168.1.50'  
PORT = 65432

print(f"Attempting to connect to Raspberry Pi at {PI_IP_ADDRESS}...")

try:
    # 2. Establish connection to the Pi
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((PI_IP_ADDRESS, PORT))
        print("Connected to Pi successfully!")
        print("Commands: [1] Turn on LED 1 | [2] Turn on LED 2 | [0] Turn off all | [q] Quit")

        # 3. Keep sending numbers until you type 'q'
        while True:
            user_input = input("Enter number/command for LEDs: ").strip()

            if user_input.lower() == 'q':
                print("Closing connection.")
                break

            if user_input in ['0', '1', '2']:
                # Encode text into raw bytes and send over the network
                client_socket.sendall(user_input.encode('utf-8'))
                print(f"Sent '{user_input}' to Pi.")
            else:
                print("Invalid input. Please enter 0, 1, 2, or q.")

except ConnectionRefusedError:
    print("\nError: Could not connect to the Pi.")
    print("Make sure the Pi script is running first and the IP address is correct.")
except Exception as e:
    print(f"\nAn error occurred: {e}")
