import sys
from gpiozero import LED

# Define the LED pins using their GPIO numbers
led1 = LED(17)
led2 = LED(27)

# Ensure both LEDs start turned off
led1.off()
led2.off()

print("--- Raspberry Pi LED Controller ---")
print("Commands: [1] Turn on LED 1 | [2] Turn on LED 2 | [0] Turn off all | [q] Quit")

try:
    while True:
        # Get input from the terminal
        user_input = input("Enter command: ").strip()
        
        if user_input.lower() == 'q':
            print("Exiting program and cleaning up pins...")
            break
            
        elif user_input == '1':
            led1.on()
            led2.off()
            print("LED 1 is ON, LED 2 is OFF")
            
        elif user_input == '2':
            led1.off()
            led2.on()
            print("LED 1 is OFF, LED 2 is ON")
            
        elif user_input == '0':
            led1.off()
            led2.off()
            print("All LEDs are OFF")
            
        else:
            print("Invalid input. Please enter 0, 1, 2, or q.")

except KeyboardInterrupt:
    print("\nProgram forced to stop.")
    
finally:
    # Ensure LEDs are turned off when exiting
    led1.off()
    led2.off()
